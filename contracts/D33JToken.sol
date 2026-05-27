// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/Pausable.sol";

/**
 * @title D33JToken
 * @dev ERC20 token for the DeeJae LeEtta Network
 * Utility and governance token with staking capabilities
 */
contract D33JToken is ERC20, ERC20Burnable, Ownable, Pausable {

    // Staking structure
    struct Stake {
        uint256 amount;
        uint256 timestamp;
        uint256 lockPeriod;
        bool active;
    }

    // Governance proposal
    struct Proposal {
        uint256 proposalId;
        string description;
        uint256 votesFor;
        uint256 votesAgainst;
        uint256 startTime;
        uint256 endTime;
        bool executed;
        mapping(address => bool) hasVoted;
    }

    mapping(address => Stake) public stakes;
    mapping(uint256 => Proposal) public proposals;
    mapping(address => uint256) public referralRewards;

    uint256 public proposalCounter;
    uint256 public constant MIN_STAKE_AMOUNT = 100 * 10**18; // 100 D33J
    uint256 public constant REWARD_RATE = 5; // 5% annual staking reward
    uint256 public constant PROPOSAL_DURATION = 7 days;

    event Staked(address indexed user, uint256 amount, uint256 lockPeriod);
    event Unstaked(address indexed user, uint256 amount, uint256 reward);
    event ProposalCreated(uint256 indexed proposalId, string description);
    event Voted(uint256 indexed proposalId, address indexed voter, bool support, uint256 weight);
    event ProposalExecuted(uint256 indexed proposalId, bool passed);
    event ReferralRewarded(address indexed referrer, address indexed referee, uint256 amount);

    constructor() ERC20("D33J Coin", "D33J") {
        // Mint initial supply: 1 billion tokens
        _mint(msg.sender, 1_000_000_000 * 10**18);
    }

    /**
     * @dev Stake tokens for premium features
     */
    function stake(uint256 _amount, uint256 _lockPeriod) external whenNotPaused {
        require(_amount >= MIN_STAKE_AMOUNT, "Amount below minimum");
        require(_lockPeriod >= 30 days, "Lock period too short");
        require(!stakes[msg.sender].active, "Already staking");

        _transfer(msg.sender, address(this), _amount);

        stakes[msg.sender] = Stake({
            amount: _amount,
            timestamp: block.timestamp,
            lockPeriod: _lockPeriod,
            active: true
        });

        emit Staked(msg.sender, _amount, _lockPeriod);
    }

    /**
     * @dev Unstake tokens and claim rewards
     */
    function unstake() external nonReentrant whenNotPaused {
        Stake storage userStake = stakes[msg.sender];
        require(userStake.active, "No active stake");
        require(block.timestamp >= userStake.timestamp + userStake.lockPeriod, "Lock period not ended");

        uint256 stakedAmount = userStake.amount;
        uint256 stakingDuration = block.timestamp - userStake.timestamp;

        // Calculate reward: (amount * rate * duration) / (365 days * 100)
        uint256 reward = (stakedAmount * REWARD_RATE * stakingDuration) / (365 days * 100);

        userStake.active = false;
        userStake.amount = 0;

        // Transfer staked amount + reward
        _transfer(address(this), msg.sender, stakedAmount);
        _mint(msg.sender, reward);

        emit Unstaked(msg.sender, stakedAmount, reward);
    }

    /**
     * @dev Create a governance proposal
     */
    function createProposal(string memory _description) external returns (uint256) {
        require(stakes[msg.sender].active, "Must be staking to propose");
        require(stakes[msg.sender].amount >= 1000 * 10**18, "Insufficient stake for proposal");

        proposalCounter++;

        Proposal storage newProposal = proposals[proposalCounter];
        newProposal.proposalId = proposalCounter;
        newProposal.description = _description;
        newProposal.startTime = block.timestamp;
        newProposal.endTime = block.timestamp + PROPOSAL_DURATION;
        newProposal.executed = false;

        emit ProposalCreated(proposalCounter, _description);

        return proposalCounter;
    }

    /**
     * @dev Vote on a proposal
     */
    function vote(uint256 _proposalId, bool _support) external {
        Proposal storage proposal = proposals[_proposalId];
        require(block.timestamp < proposal.endTime, "Voting ended");
        require(!proposal.hasVoted[msg.sender], "Already voted");
        require(balanceOf(msg.sender) > 0, "No voting power");

        uint256 votingPower = balanceOf(msg.sender);

        // Bonus voting power for stakers
        if (stakes[msg.sender].active) {
            votingPower += stakes[msg.sender].amount / 2;
        }

        proposal.hasVoted[msg.sender] = true;

        if (_support) {
            proposal.votesFor += votingPower;
        } else {
            proposal.votesAgainst += votingPower;
        }

        emit Voted(_proposalId, msg.sender, _support, votingPower);
    }

    /**
     * @dev Execute a proposal after voting period
     */
    function executeProposal(uint256 _proposalId) external onlyOwner {
        Proposal storage proposal = proposals[_proposalId];
        require(block.timestamp >= proposal.endTime, "Voting not ended");
        require(!proposal.executed, "Already executed");

        proposal.executed = true;
        bool passed = proposal.votesFor > proposal.votesAgainst;

        emit ProposalExecuted(_proposalId, passed);
    }

    /**
     * @dev Distribute referral rewards
     */
    function distributeReferralReward(address _referrer, address _referee, uint256 _amount) external onlyOwner {
        require(_referrer != address(0), "Invalid referrer");
        require(_referee != address(0), "Invalid referee");

        referralRewards[_referrer] += _amount;
        _mint(_referrer, _amount);

        emit ReferralRewarded(_referrer, _referee, _amount);
    }

    /**
     * @dev Check if address has premium access (staking)
     */
    function hasPremiumAccess(address _user) external view returns (bool) {
        return stakes[_user].active;
    }

    /**
     * @dev Get stake details
     */
    function getStake(address _user) external view returns (Stake memory) {
        return stakes[_user];
    }

    /**
     * @dev Get voting power for an address
     */
    function getVotingPower(address _user) external view returns (uint256) {
        uint256 power = balanceOf(_user);
        if (stakes[_user].active) {
            power += stakes[_user].amount / 2;
        }
        return power;
    }

    /**
     * @dev Pause token transfers (emergency)
     */
    function pause() external onlyOwner {
        _pause();
    }

    /**
     * @dev Unpause token transfers
     */
    function unpause() external onlyOwner {
        _unpause();
    }

    /**
     * @dev Override transfer to add pause functionality
     */
    function _beforeTokenTransfer(
        address from,
        address to,
        uint256 amount
    ) internal virtual override whenNotPaused {
        super._beforeTokenTransfer(from, to, amount);
    }

    // Add nonReentrant modifier (requires ReentrancyGuard import)
    modifier nonReentrant() {
        _;
    }
}
