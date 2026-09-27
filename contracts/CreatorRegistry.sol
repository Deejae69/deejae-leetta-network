// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";

contract CreatorRegistry is Ownable {
    struct CreatorProfile {
        string username;
        string category;
        string metadataURI;
        address wallet;
        bool verified;
        uint256 registeredAt;
    }

    mapping(address => CreatorProfile) public creators;
    mapping(string => address) public usernameToAddress;
    address[] public creatorAddresses;

    event CreatorRegistered(
        address indexed wallet,
        string username,
        string category,
        bool verified
    );

    event CreatorVerified(address indexed wallet, bool verified);

    constructor() Ownable(msg.sender) {}

    function registerCreator(
        string calldata username,
        string calldata category,
        string calldata metadataURI
    ) external {
        require(bytes(username).length > 0, "Username required");
        require(bytes(category).length > 0, "Category required");
        require(creators[msg.sender].wallet == address(0), "Already registered");
        require(usernameToAddress[username] == address(0), "Username taken");

        creators[msg.sender] = CreatorProfile({
            username: username,
            category: category,
            metadataURI: metadataURI,
            wallet: msg.sender,
            verified: false,
            registeredAt: block.timestamp
        });

        usernameToAddress[username] = msg.sender;
        creatorAddresses.push(msg.sender);

        emit CreatorRegistered(msg.sender, username, category, false);
    }

    function verifyCreator(address creatorAddress) external onlyOwner {
        require(creators[creatorAddress].wallet != address(0), "Creator not found");
        creators[creatorAddress].verified = true;
        emit CreatorVerified(creatorAddress, true);
    }

    function getCreator(address creatorAddress)
        external
        view
        returns (CreatorProfile memory)
    {
        return creators[creatorAddress];
    }

    function getCreatorCount() external view returns (uint256) {
        return creatorAddresses.length;
    }
}
