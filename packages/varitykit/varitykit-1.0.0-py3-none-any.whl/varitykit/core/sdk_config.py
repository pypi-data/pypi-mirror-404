"""
SDK Configuration Module
Manages network configurations and credentials for Varity SDK integration
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import yaml  # type: ignore[import-untyped]


@dataclass
class NetworkConfig:
    """Network configuration for blockchain deployments"""

    name: str
    chain_id: int
    rpc_url: str
    explorer_url: str
    is_testnet: bool


@dataclass
class AkashNetworkConfig:
    """Akash Network configuration"""

    rpc_endpoint: str
    chain_id: str
    api_endpoint: str
    faucet_url: Optional[str] = None


@dataclass
class FilecoinNetworkConfig:
    """Filecoin/Pinata configuration"""

    pinata_api_url: str
    pinata_gateway: str
    api_key_env: str = "PINATA_API_KEY"
    secret_env: str = "PINATA_API_SECRET"


@dataclass
class CelestiaNetworkConfig:
    """Celestia DA configuration"""

    rpc_endpoint: str
    network: str
    auth_token_env: str = "CELESTIA_AUTH_TOKEN"


@dataclass
class LitProtocolConfig:
    """Lit Protocol configuration"""

    network: str


class SDKConfig:
    """
    Configuration manager for Varity SDK integration

    Loads network-specific configurations from YAML files and
    provides typed access to all SDK configuration parameters.
    """

    def __init__(self, network: str = "testnet"):
        """
        Initialize SDK configuration

        Args:
            network: Network to use ('testnet', 'mainnet', or 'local')
        """
        self.network = network
        self.config_dir = Path(__file__).parent.parent / "config"
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """Load network configuration from YAML file"""
        config_path = self.config_dir / f"{self.network}.yaml"

        if not config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {config_path}\n"
                f"Available networks: testnet, mainnet, local"
            )

        with open(config_path, "r") as f:
            result: Dict[Any, Any] = yaml.safe_load(f)
            return result

    def get_blockchain_config(self) -> NetworkConfig:
        """Get blockchain network configuration for Varity L3"""
        # Use Varity L3 (Chain ID 33529) as primary network for MVP
        # Fall back to arbitrum only if varity config doesn't exist
        if "varity" in self.config["networks"]:
            net_config = self.config["networks"]["varity"]
        else:
            net_config = self.config["networks"]["arbitrum"]

        # Substitute environment variables in RPC URL
        rpc_url = net_config["rpc"]
        if "${" in rpc_url:
            # Extract variable name (e.g., ${ALCHEMY_API_KEY})
            import re

            for match in re.finditer(r"\$\{([^}]+)\}", rpc_url):
                var_name = match.group(1)
                var_value = os.getenv(var_name, "")
                rpc_url = rpc_url.replace(f"${{{var_name}}}", var_value)

        return NetworkConfig(
            name=net_config.get("name", f"Arbitrum {self.network.capitalize()}"),
            chain_id=net_config["chainId"],
            rpc_url=rpc_url,
            explorer_url=net_config["explorer"],
            is_testnet=self.network != "mainnet",
        )

    def get_contract_config(self) -> Dict:
        """Get contract deployment configuration"""
        return {
            "network": self.network,
            "rpc_url": self.get_blockchain_config().rpc_url,
            "chain_id": self.get_blockchain_config().chain_id,
            "private_key": os.getenv("WALLET_PRIVATE_KEY"),
            "explorer_api_key": os.getenv("ARBISCAN_API_KEY"),
            "verify_contracts": self.network != "local",
        }

    def get_akash_config(self) -> AkashNetworkConfig:
        """Get Akash Network configuration"""
        akash_config = self.config["depin"]["akash"]

        return AkashNetworkConfig(
            rpc_endpoint=akash_config["rpc"],
            chain_id=akash_config["chainId"],
            api_endpoint=akash_config.get("api", akash_config["rpc"]),
            faucet_url=akash_config.get("faucet"),
        )

    def get_filecoin_config(self) -> FilecoinNetworkConfig:
        """Get Filecoin/Pinata configuration"""
        filecoin_config = self.config["depin"]["filecoin"]["pinata"]

        return FilecoinNetworkConfig(
            pinata_api_url=filecoin_config["api"], pinata_gateway=filecoin_config["gateway"]
        )

    def get_celestia_config(self) -> CelestiaNetworkConfig:
        """Get Celestia DA configuration"""
        celestia_config = self.config["depin"]["celestia"]

        return CelestiaNetworkConfig(
            rpc_endpoint=celestia_config["rpc"], network=celestia_config["network"]
        )

    def get_lit_config(self) -> LitProtocolConfig:
        """Get Lit Protocol configuration"""
        lit_config = self.config["depin"]["lit"]

        return LitProtocolConfig(network=lit_config["network"])

    def get_deployed_contracts(self) -> Dict[str, str]:
        """Get deployed contract addresses for this network"""
        result: Dict[str, str] = self.config.get("contracts", {})
        return result

    def validate_environment(self) -> Dict[str, bool]:
        """
        Validate that all required environment variables are set

        Returns:
            Dictionary mapping requirement names to validation status
        """
        validations = {}

        # Check wallet private key
        validations["wallet_private_key"] = bool(os.getenv("WALLET_PRIVATE_KEY"))

        # Check Pinata credentials
        validations["pinata_api_key"] = bool(os.getenv("PINATA_API_KEY"))
        validations["pinata_api_secret"] = bool(os.getenv("PINATA_API_SECRET"))

        # Check Akash wallet (optional for read-only)
        validations["akash_wallet"] = bool(
            os.getenv("AKASH_WALLET_MNEMONIC") or os.getenv("AKASH_WALLET_ADDRESS")
        )

        # Check Celestia auth token (optional for some operations)
        validations["celestia_auth"] = bool(os.getenv("CELESTIA_AUTH_TOKEN"))

        # Check Arbiscan API key (only required for contract verification)
        if self.config.get("contract_config", {}).get("verify_contracts", True):
            validations["arbiscan_api_key"] = bool(os.getenv("ARBISCAN_API_KEY"))

        return validations

    def get_missing_env_vars(self):
        """Get list of missing required environment variables"""
        validations = self.validate_environment()
        required = ["wallet_private_key", "pinata_api_key", "pinata_api_secret"]

        missing = []
        for var in required:
            if not validations.get(var):
                env_var_name = {
                    "wallet_private_key": "WALLET_PRIVATE_KEY",
                    "pinata_api_key": "PINATA_API_KEY",
                    "pinata_api_secret": "PINATA_API_SECRET",
                }.get(var, var.upper())
                missing.append(env_var_name)

        return missing

    def is_valid(self) -> bool:
        """Check if configuration is valid and complete"""
        missing = self.get_missing_env_vars()
        return len(missing) == 0

    def get_sdk_base_path(self) -> Path:
        """Get path to varity-core-backend SDK package"""
        # Navigate from varitykit-cli to packages/varity-core-backend
        cli_root = Path(__file__).parent.parent.parent
        sdk_path = cli_root.parent / "packages" / "varity-core-backend"

        if not sdk_path.exists():
            raise FileNotFoundError(
                f"Varity SDK not found at: {sdk_path}\n"
                f"Please ensure varity-core-backend package is installed"
            )

        return sdk_path

    def __repr__(self) -> str:
        return (
            f"SDKConfig(network={self.network}, "
            f"chain_id={self.get_blockchain_config().chain_id}, "
            f"valid={self.is_valid()})"
        )
