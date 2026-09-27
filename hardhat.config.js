// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

contract CreatorMarketplace is Ownable {
    struct Listing {
        uint256 id;
        address seller;
        string itemName;
        string itemType;
        string metadataURI;
        uint256 price;
        address paymentToken;
        bool active;
    }

    uint256 public nextListingId;
    mapping(uint256 => Listing) public listings;

    event Listed(
        uint256 indexed listingId,
        address indexed seller,
        string itemName,
        uint256 price
    );

    event Purchased(
        uint256 indexed listingId,
        address indexed buyer,
        address indexed seller
    );

    constructor() Ownable(msg.sender) {}

    function listItem(
        string calldata itemName,
        string calldata itemType,
        string calldata metadataURI,
        uint256 price,
        address paymentToken
    ) external {
        require(bytes(itemName).length > 0, "Item name is required");
        require(price > 0, "Price must be greater than zero");
        require(paymentToken != address(0), "Invalid token");

        listings[nextListingId] = Listing({
            id: nextListingId,
            seller: msg.sender,
            itemName: itemName,
            itemType: itemType,
            metadataURI: metadataURI,
            price: price,
            paymentToken: paymentToken,
            active: true
        });

        emit Listed(nextListingId, msg.sender, itemName, price);
        nextListingId += 1;
    }

    function buyItem(uint256 listingId) external {
        Listing storage item = listings[listingId];
        require(item.active, "Listing not active");
        require(item.seller != msg.sender, "Seller cannot buy own item");

        IERC20 token = IERC20(item.paymentToken);
        require(token.transferFrom(msg.sender, item.seller, item.price), "Transfer failed");

        item.active = false;
        emit Purchased(listingId, msg.sender, item.seller);
    }

    function deactivateListing(uint256 listingId) external {
        require(listings[listingId].seller == msg.sender, "Not authorized");
        listings[listingId].active = false;
    }
}
