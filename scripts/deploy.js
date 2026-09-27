const { ethers } = require("hardhat");

async function main() {
  const [deployer] = await ethers.getSigners();

  console.log("Deploying contracts with:", deployer.address);

  const D33JToken = await ethers.getContractFactory("D33JToken");
  const token = await D33JToken.deploy();
  await token.waitForDeployment();

  const CreatorRegistry = await ethers.getContractFactory("CreatorRegistry");
  const registry = await CreatorRegistry.deploy();
  await registry.waitForDeployment();

  const CreatorMarketplace = await ethers.getContractFactory("CreatorMarketplace");
  const marketplace = await CreatorMarketplace.deploy();
  await marketplace.waitForDeployment();

  console.log("D33JToken deployed to:", await token.getAddress());
  console.log("CreatorRegistry deployed to:", await registry.getAddress());
  console.log("CreatorMarketplace deployed to:", await marketplace.getAddress());
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
