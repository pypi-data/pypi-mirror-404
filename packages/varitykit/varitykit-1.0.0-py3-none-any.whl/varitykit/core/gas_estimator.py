"""
Gas Estimator Module
Estimates gas costs for contract deployments and transactions
"""

import asyncio
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional

from web3 import Web3
from web3.exceptions import Web3Exception

from .sdk_config import SDKConfig

logger = logging.getLogger(__name__)


@dataclass
class GasEstimate:
    """Gas estimation result"""

    gas_units: int
    gas_price_gwei: float
    total_wei: int
    total_eth: float
    total_usd: float
    operation: str


@dataclass
class DeploymentCostEstimate:
    """Complete deployment cost estimation"""

    contracts: Dict[str, GasEstimate]
    total_gas_units: int
    total_eth: float
    total_usd: float
    breakdown: Dict[str, float]


class GasEstimator:
    """
    Estimates gas costs for blockchain operations

    Connects to the blockchain network and provides accurate
    gas estimations for contract deployments and transactions.
    """

    def __init__(self, network: str = "testnet", eth_usd_price: Optional[float] = None):
        """
        Initialize gas estimator

        Args:
            network: Target network
            eth_usd_price: ETH/USD price override (fetched from API if not provided)
        """
        self.network = network
        self.config = SDKConfig(network)
        self.blockchain_config = self.config.get_blockchain_config()

        # Initialize Web3 connection
        self.w3 = Web3(Web3.HTTPProvider(self.blockchain_config.rpc_url))

        # Check connection
        if not self.w3.is_connected():
            logger.warning(f"Failed to connect to {self.blockchain_config.rpc_url}")

        # ETH price
        self.eth_usd_price = eth_usd_price or self._fetch_eth_price()

        logger.info(f"GasEstimator initialized for {network}")

    def _fetch_eth_price(self) -> float:
        """Fetch current ETH/USD price"""
        # For testnets, return 0
        if self.blockchain_config.is_testnet:
            return 0.0

        # For mainnet, could fetch from CoinGecko/CoinMarketCap API
        # For now, return a default estimate
        return 2000.0  # Conservative estimate

    async def get_current_gas_price(self) -> int:
        """
        Get current gas price from network

        Returns:
            Gas price in wei
        """
        try:
            if not self.w3.is_connected():
                logger.warning("Web3 not connected, using fallback gas price")
                # Fallback: Arbitrum typical gas price is ~0.1 gwei
                return Web3.to_wei(0.1, "gwei")

            fee_data = self.w3.eth.fee_history(1, "latest")
            base_fee = fee_data["baseFeePerGas"][-1]

            # Add priority fee (typical 0.01 gwei on Arbitrum)
            priority_fee = Web3.to_wei(0.01, "gwei")

            total_gas_price = base_fee + priority_fee

            logger.debug(f'Current gas price: {Web3.from_wei(total_gas_price, "gwei")} gwei')

            return total_gas_price

        except Web3Exception as e:
            logger.error(f"Failed to fetch gas price: {e}")
            # Fallback to config default
            return Web3.to_wei(self.config.config["gas"]["price"]["standard"], "gwei")

    def estimate_contract_deployment(
        self,
        contract_name: str,
        bytecode: Optional[str] = None,
        constructor_args: Optional[List] = None,
    ) -> GasEstimate:
        """
        Estimate gas for contract deployment

        Args:
            contract_name: Name of contract to deploy
            bytecode: Contract bytecode (if not provided, uses estimate)
            constructor_args: Constructor arguments

        Returns:
            Gas estimation
        """
        # Predefined gas estimates for common contracts
        # These are based on typical deployments
        CONTRACT_GAS_ESTIMATES = {
            "DashboardRegistry": 3_500_000,
            "TemplateManager": 2_800_000,
            "AccessControl": 2_200_000,
            "BillingModule": 3_000_000,
            "ZKMLVerifier": 4_500_000,
            "OracleClient": 2_500_000,
        }

        gas_estimate = CONTRACT_GAS_ESTIMATES.get(contract_name, 3_000_000)

        # If bytecode provided, try to estimate based on size
        if bytecode:
            # Rough estimate: 200 gas per byte of bytecode
            bytecode_size = len(bytecode) // 2  # Convert hex to bytes
            gas_estimate = bytecode_size * 200

        # Add buffer for constructor execution
        if constructor_args and len(constructor_args) > 0:
            gas_estimate += 50_000 * len(constructor_args)

        # Get current gas price
        gas_price = asyncio.run(self.get_current_gas_price())
        gas_price_gwei = Web3.from_wei(gas_price, "gwei")

        total_wei = gas_estimate * gas_price
        total_eth = Web3.from_wei(total_wei, "ether")
        total_usd = float(total_eth) * self.eth_usd_price

        return GasEstimate(
            gas_units=gas_estimate,
            gas_price_gwei=float(gas_price_gwei),
            total_wei=total_wei,
            total_eth=float(total_eth),
            total_usd=total_usd,
            operation=f"Deploy {contract_name}",
        )

    def estimate_transaction(
        self, operation: str, estimated_gas: Optional[int] = None
    ) -> GasEstimate:
        """
        Estimate gas for a transaction

        Args:
            operation: Description of operation
            estimated_gas: Gas estimate (if not provided, uses default)

        Returns:
            Gas estimation
        """
        # Default gas estimates for common operations
        OPERATION_GAS_ESTIMATES = {
            "registerDashboard": 300_000,
            "grantAccess": 100_000,
            "recordUsage": 80_000,
            "updateTemplate": 150_000,
            "setPermissions": 120_000,
        }

        gas_estimate = estimated_gas or 100_000

        # Try to find operation in predefined estimates
        for op_name, gas in OPERATION_GAS_ESTIMATES.items():
            if op_name.lower() in operation.lower():
                gas_estimate = gas
                break

        gas_price = asyncio.run(self.get_current_gas_price())
        gas_price_gwei = Web3.from_wei(gas_price, "gwei")

        total_wei = gas_estimate * gas_price
        total_eth = Web3.from_wei(total_wei, "ether")
        total_usd = float(total_eth) * self.eth_usd_price

        return GasEstimate(
            gas_units=gas_estimate,
            gas_price_gwei=float(gas_price_gwei),
            total_wei=total_wei,
            total_eth=float(total_eth),
            total_usd=total_usd,
            operation=operation,
        )

    def estimate_full_deployment(
        self, contract_names: List[str], include_registration: bool = True
    ) -> DeploymentCostEstimate:
        """
        Estimate total cost for complete deployment

        Args:
            contract_names: List of contracts to deploy
            include_registration: Include dashboard registration cost

        Returns:
            Complete deployment cost estimate
        """
        contract_estimates = {}
        total_gas = 0

        # Estimate each contract deployment
        for contract_name in contract_names:
            estimate = self.estimate_contract_deployment(contract_name)
            contract_estimates[contract_name] = estimate
            total_gas += estimate.gas_units

        # Add registration transaction if requested
        if include_registration:
            reg_estimate = self.estimate_transaction("registerDashboard")
            contract_estimates["Dashboard Registration"] = reg_estimate
            total_gas += reg_estimate.gas_units

        # Calculate totals
        gas_price = asyncio.run(self.get_current_gas_price())
        total_wei = total_gas * gas_price
        total_eth = Web3.from_wei(total_wei, "ether")
        total_usd = float(total_eth) * self.eth_usd_price

        # Create breakdown
        breakdown = {}
        for name, estimate in contract_estimates.items():
            breakdown[name] = estimate.total_usd

        return DeploymentCostEstimate(
            contracts=contract_estimates,
            total_gas_units=total_gas,
            total_eth=float(total_eth),
            total_usd=total_usd,
            breakdown=breakdown,
        )

    def format_estimate(self, estimate: GasEstimate) -> str:
        """
        Format gas estimate as human-readable string

        Args:
            estimate: Gas estimate to format

        Returns:
            Formatted string
        """
        if self.blockchain_config.is_testnet:
            return (
                f"{estimate.operation}:\n"
                f"  Gas Units: {estimate.gas_units:,}\n"
                f"  Gas Price: {estimate.gas_price_gwei:.4f} gwei\n"
                f"  Total Cost: {estimate.total_eth:.8f} ETH (testnet - free)"
            )
        else:
            return (
                f"{estimate.operation}:\n"
                f"  Gas Units: {estimate.gas_units:,}\n"
                f"  Gas Price: {estimate.gas_price_gwei:.4f} gwei\n"
                f"  Total Cost: {estimate.total_eth:.8f} ETH (${estimate.total_usd:.2f} USD)"
            )

    def format_deployment_estimate(self, estimate: DeploymentCostEstimate) -> str:
        """
        Format complete deployment estimate

        Args:
            estimate: Deployment cost estimate

        Returns:
            Formatted string
        """
        lines = ["Deployment Cost Estimate:", ""]

        for name, gas_est in estimate.contracts.items():
            lines.append(f"  {name}:")
            lines.append(f"    Gas: {gas_est.gas_units:,} units")
            if not self.blockchain_config.is_testnet:
                lines.append(f"    Cost: {gas_est.total_eth:.6f} ETH (${gas_est.total_usd:.2f})")
            lines.append("")

        lines.append("Total:")
        lines.append(f"  Gas Units: {estimate.total_gas_units:,}")

        if self.blockchain_config.is_testnet:
            lines.append(f"  Cost: {estimate.total_eth:.6f} ETH (testnet - free)")
        else:
            lines.append(f"  Cost: {estimate.total_eth:.6f} ETH (${estimate.total_usd:.2f} USD)")

        return "\n".join(lines)
