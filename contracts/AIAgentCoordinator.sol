// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

/**
 * @title AIAgentCoordinator
 * @dev Smart contract for coordinating AI agents in the DeeJae LeEtta Network
 * Manages agent registration, task assignment, performance tracking, and D33J token rewards
 */
contract AIAgentCoordinator is Ownable, ReentrancyGuard {

    IERC20 public d33jToken;

    // Agent types
    enum AgentType { MMO_CUSTOMER, ECOMMERCE_CLIENT, ARTS_MUSIC, INVESTOR_RELATIONS }

    // Agent status
    enum AgentStatus { INACTIVE, ACTIVE, PAUSED, RETIRED }

    // Task status
    enum TaskStatus { PENDING, IN_PROGRESS, COMPLETED, FAILED }

    struct Agent {
        address agentAddress;
        AgentType agentType;
        AgentStatus status;
        uint256 reputationScore;
        uint256 tasksCompleted;
        uint256 totalRewardsEarned;
        uint256 registrationTime;
        string metadataURI;
    }

    struct Task {
        uint256 taskId;
        AgentType requiredAgentType;
        address assignedAgent;
        TaskStatus status;
        uint256 rewardAmount;
        uint256 createdAt;
        uint256 completedAt;
        string taskDataURI;
        bytes32 taskHash;
    }

    struct Performance {
        uint256 successRate;
        uint256 averageCompletionTime;
        uint256 qualityScore;
        uint256 lastUpdated;
    }

    // Mappings
    mapping(address => Agent) public agents;
    mapping(uint256 => Task) public tasks;
    mapping(address => Performance) public agentPerformance;
    mapping(AgentType => address[]) public agentsByType;
    mapping(address => uint256[]) public agentTasks;

    // State variables
    uint256 public taskCounter;
    uint256 public minReputationForTasks = 50;
    uint256 public baseRewardAmount = 100 * 10**18; // 100 D33J tokens

    // Events
    event AgentRegistered(address indexed agentAddress, AgentType agentType, uint256 timestamp);
    event AgentStatusChanged(address indexed agentAddress, AgentStatus newStatus);
    event TaskCreated(uint256 indexed taskId, AgentType agentType, uint256 rewardAmount);
    event TaskAssigned(uint256 indexed taskId, address indexed agentAddress);
    event TaskCompleted(uint256 indexed taskId, address indexed agentAddress, uint256 rewardAmount);
    event TaskFailed(uint256 indexed taskId, address indexed agentAddress);
    event ReputationUpdated(address indexed agentAddress, uint256 newReputation);
    event RewardDistributed(address indexed agentAddress, uint256 amount);

    constructor(address _d33jToken) {
        d33jToken = IERC20(_d33jToken);
    }

    /**
     * @dev Register a new AI agent
     */
    function registerAgent(
        AgentType _agentType,
        string memory _metadataURI
    ) external {
        require(agents[msg.sender].agentAddress == address(0), "Agent already registered");

        agents[msg.sender] = Agent({
            agentAddress: msg.sender,
            agentType: _agentType,
            status: AgentStatus.ACTIVE,
            reputationScore: 100, // Starting reputation
            tasksCompleted: 0,
            totalRewardsEarned: 0,
            registrationTime: block.timestamp,
            metadataURI: _metadataURI
        });

        agentsByType[_agentType].push(msg.sender);

        emit AgentRegistered(msg.sender, _agentType, block.timestamp);
    }

    /**
     * @dev Create a new task for AI agents
     */
    function createTask(
        AgentType _agentType,
        uint256 _rewardAmount,
        string memory _taskDataURI,
        bytes32 _taskHash
    ) external onlyOwner returns (uint256) {
        require(_rewardAmount > 0, "Reward must be positive");

        taskCounter++;

        tasks[taskCounter] = Task({
            taskId: taskCounter,
            requiredAgentType: _agentType,
            assignedAgent: address(0),
            status: TaskStatus.PENDING,
            rewardAmount: _rewardAmount,
            createdAt: block.timestamp,
            completedAt: 0,
            taskDataURI: _taskDataURI,
            taskHash: _taskHash
        });

        emit TaskCreated(taskCounter, _agentType, _rewardAmount);

        return taskCounter;
    }

    /**
     * @dev Assign task to an agent
     */
    function assignTask(uint256 _taskId, address _agentAddress) external onlyOwner {
        Task storage task = tasks[_taskId];
        Agent storage agent = agents[_agentAddress];

        require(task.status == TaskStatus.PENDING, "Task not available");
        require(agent.status == AgentStatus.ACTIVE, "Agent not active");
        require(agent.agentType == task.requiredAgentType, "Agent type mismatch");
        require(agent.reputationScore >= minReputationForTasks, "Insufficient reputation");

        task.assignedAgent = _agentAddress;
        task.status = TaskStatus.IN_PROGRESS;
        agentTasks[_agentAddress].push(_taskId);

        emit TaskAssigned(_taskId, _agentAddress);
    }

    /**
     * @dev Complete a task and distribute rewards
     */
    function completeTask(
        uint256 _taskId,
        uint256 _qualityScore
    ) external onlyOwner nonReentrant {
        Task storage task = tasks[_taskId];
        Agent storage agent = agents[task.assignedAgent];

        require(task.status == TaskStatus.IN_PROGRESS, "Task not in progress");
        require(_qualityScore <= 100, "Quality score must be <= 100");

        task.status = TaskStatus.COMPLETED;
        task.completedAt = block.timestamp;

        // Update agent stats
        agent.tasksCompleted++;

        // Calculate reward based on quality score
        uint256 rewardAmount = (task.rewardAmount * _qualityScore) / 100;
        agent.totalRewardsEarned += rewardAmount;

        // Update reputation (weighted average)
        agent.reputationScore = (agent.reputationScore * 9 + _qualityScore) / 10;

        // Update performance metrics
        _updatePerformance(task.assignedAgent, _taskId, _qualityScore, true);

        // Distribute reward
        require(d33jToken.transfer(task.assignedAgent, rewardAmount), "Reward transfer failed");

        emit TaskCompleted(_taskId, task.assignedAgent, rewardAmount);
        emit ReputationUpdated(task.assignedAgent, agent.reputationScore);
        emit RewardDistributed(task.assignedAgent, rewardAmount);
    }

    /**
     * @dev Mark task as failed
     */
    function failTask(uint256 _taskId) external onlyOwner {
        Task storage task = tasks[_taskId];
        Agent storage agent = agents[task.assignedAgent];

        require(task.status == TaskStatus.IN_PROGRESS, "Task not in progress");

        task.status = TaskStatus.FAILED;

        // Penalize reputation
        if (agent.reputationScore > 10) {
            agent.reputationScore -= 10;
        }

        // Update performance metrics
        _updatePerformance(task.assignedAgent, _taskId, 0, false);

        emit TaskFailed(_taskId, task.assignedAgent);
        emit ReputationUpdated(task.assignedAgent, agent.reputationScore);
    }

    /**
     * @dev Update agent performance metrics
     */
    function _updatePerformance(
        address _agentAddress,
        uint256 _taskId,
        uint256 _qualityScore,
        bool _success
    ) internal {
        Performance storage perf = agentPerformance[_agentAddress];
        Task storage task = tasks[_taskId];

        uint256 completionTime = block.timestamp - task.createdAt;

        if (_success) {
            // Update success rate
            uint256 totalTasks = agents[_agentAddress].tasksCompleted;
            perf.successRate = ((perf.successRate * (totalTasks - 1)) + 100) / totalTasks;

            // Update average completion time
            perf.averageCompletionTime = ((perf.averageCompletionTime * (totalTasks - 1)) + completionTime) / totalTasks;

            // Update quality score
            perf.qualityScore = ((perf.qualityScore * (totalTasks - 1)) + _qualityScore) / totalTasks;
        } else {
            uint256 totalAttempts = agents[_agentAddress].tasksCompleted + 1;
            perf.successRate = (perf.successRate * (totalAttempts - 1)) / totalAttempts;
        }

        perf.lastUpdated = block.timestamp;
    }

    /**
     * @dev Change agent status
     */
    function updateAgentStatus(address _agentAddress, AgentStatus _newStatus) external onlyOwner {
        agents[_agentAddress].status = _newStatus;
        emit AgentStatusChanged(_agentAddress, _newStatus);
    }

    /**
     * @dev Get agent details
     */
    function getAgent(address _agentAddress) external view returns (Agent memory) {
        return agents[_agentAddress];
    }

    /**
     * @dev Get task details
     */
    function getTask(uint256 _taskId) external view returns (Task memory) {
        return tasks[_taskId];
    }

    /**
     * @dev Get agent performance
     */
    function getPerformance(address _agentAddress) external view returns (Performance memory) {
        return agentPerformance[_agentAddress];
    }

    /**
     * @dev Get all agents of a specific type
     */
    function getAgentsByType(AgentType _agentType) external view returns (address[] memory) {
        return agentsByType[_agentType];
    }

    /**
     * @dev Get all tasks assigned to an agent
     */
    function getAgentTasks(address _agentAddress) external view returns (uint256[] memory) {
        return agentTasks[_agentAddress];
    }

    /**
     * @dev Update minimum reputation requirement
     */
    function setMinReputation(uint256 _minReputation) external onlyOwner {
        minReputationForTasks = _minReputation;
    }

    /**
     * @dev Update base reward amount
     */
    function setBaseReward(uint256 _baseReward) external onlyOwner {
        baseRewardAmount = _baseReward;
    }

    /**
     * @dev Withdraw D33J tokens (emergency only)
     */
    function withdrawTokens(uint256 _amount) external onlyOwner {
        require(d33jToken.transfer(owner(), _amount), "Withdrawal failed");
    }
}
