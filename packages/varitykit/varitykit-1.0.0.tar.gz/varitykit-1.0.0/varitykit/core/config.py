"""
Configuration management for VarityKit
"""

import os
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional

import toml  # type: ignore[import-untyped]


class Environment(str, Enum):
    """Environment types"""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    LOCAL = "local"


@dataclass
class APIConfig:
    """API configuration"""

    staging_url: str = "https://staging.api.varity.io"
    production_url: str = "https://api.varity.io"
    local_url: str = "http://localhost:3001"
    timeout: int = 30
    api_key: Optional[str] = None


@dataclass
class NetworkConfig:
    """Network configuration"""

    localnet_rpc: str = "http://localhost:8545"
    testnet_rpc: str = "https://rpc-varity-testnet-rroe52pwjp.t.conduit.xyz"  # Varity L3 Testnet
    mainnet_rpc: str = "https://mainnet.varity.io"  # TODO: Update when mainnet launches
    chain_id_local: int = 31337
    chain_id_testnet: int = 33529  # Varity L3 Testnet (NOT Arbitrum Sepolia 421614)
    chain_id_mainnet: int = 42161  # Arbitrum One (for settlement layer)


@dataclass
class StorageConfig:
    """Storage configuration"""

    filecoin_gateway: str = "https://api.pinata.cloud"
    ipfs_gateway: str = "https://gateway.pinata.cloud"
    celestia_rpc: str = "https://celestia.varity.io"


@dataclass
class LoggingConfig:
    """Logging configuration"""

    level: str = "INFO"
    json_format: bool = False
    log_file: Optional[Path] = None


@dataclass
class VarityConfig:
    """Main VarityKit configuration"""

    environment: Environment = Environment.DEVELOPMENT
    project_name: Optional[str] = None
    project_path: Optional[Path] = None
    api: APIConfig = field(default_factory=APIConfig)
    network: NetworkConfig = field(default_factory=NetworkConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    wallet_address: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary"""
        config_dict = asdict(self)
        # Convert Path objects to strings
        if self.project_path:
            config_dict["project_path"] = str(self.project_path)
        if self.logging.log_file:
            config_dict["logging"]["log_file"] = str(self.logging.log_file)
        # Convert enum to string
        config_dict["environment"] = self.environment.value
        return config_dict


class ConfigManager:
    """Manages VarityKit configuration"""

    CONFIG_FILENAME = ".varitykit.toml"
    DEFAULT_CONFIG_DIR = Path.home() / ".varity"

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path
        self.config: Optional[VarityConfig] = None

    def find_config_file(self, start_path: Optional[Path] = None) -> Optional[Path]:
        """
        Find .varitykit.toml file by walking up directory tree
        Similar to how git finds .git directory
        """
        if start_path is None:
            start_path = Path.cwd()

        current = start_path.resolve()

        # Walk up directory tree
        while True:
            config_file = current / self.CONFIG_FILENAME
            if config_file.exists():
                return config_file

            # Check if we've reached root
            parent = current.parent
            if parent == current:
                break
            current = parent

        # Check global config location
        global_config = self.DEFAULT_CONFIG_DIR / self.CONFIG_FILENAME
        if global_config.exists():
            return global_config

        return None

    def load_config(self, config_path: Optional[Path] = None) -> VarityConfig:
        """Load configuration from file"""
        if config_path is None:
            config_path = self.find_config_file()

        if config_path is None:
            # Return default config if no file found
            return VarityConfig()

        try:
            with open(config_path, "r") as f:
                data = toml.load(f)

            # Parse configuration
            config = VarityConfig()

            # Environment
            if "environment" in data:
                config.environment = Environment(data["environment"])

            # Project info
            config.project_name = data.get("project_name")
            if "project_path" in data:
                config.project_path = Path(data["project_path"])

            # API config
            if "api" in data:
                config.api = APIConfig(**data["api"])

            # Network config
            if "network" in data:
                config.network = NetworkConfig(**data["network"])

            # Storage config
            if "storage" in data:
                config.storage = StorageConfig(**data["storage"])

            # Logging config
            if "logging" in data:
                logging_data = data["logging"].copy()
                if "log_file" in logging_data:
                    logging_data["log_file"] = Path(logging_data["log_file"])
                config.logging = LoggingConfig(**logging_data)

            # Wallet
            config.wallet_address = data.get("wallet_address")

            self.config = config
            return config

        except Exception as e:
            raise RuntimeError(f"Failed to load config from {config_path}: {e}")

    def save_config(self, config: VarityConfig, config_path: Optional[Path] = None) -> Path:
        """Save configuration to file"""
        if config_path is None:
            if self.config_path:
                config_path = self.config_path
            else:
                # Save to current directory
                config_path = Path.cwd() / self.CONFIG_FILENAME

        # Ensure parent directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert config to dictionary
        config_dict = config.to_dict()

        # Write to file
        with open(config_path, "w") as f:
            toml.dump(config_dict, f)

        self.config = config
        self.config_path = config_path
        return config_path

    def create_project_config(
        self,
        project_name: str,
        project_path: Path,
        environment: Environment = Environment.DEVELOPMENT,
    ) -> VarityConfig:
        """Create new project configuration"""
        config = VarityConfig(
            environment=environment, project_name=project_name, project_path=project_path
        )

        # Load API key from environment if available
        api_key = os.environ.get("VARITY_API_KEY")
        if api_key:
            config.api.api_key = api_key

        # Load wallet address from environment if available
        wallet_address = os.environ.get("VARITY_WALLET_ADDRESS")
        if wallet_address:
            config.wallet_address = wallet_address

        return config

    def update_config(self, **kwargs) -> VarityConfig:
        """Update existing configuration"""
        if self.config is None:
            self.config = self.load_config()

        # Update fields
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)

        return self.config

    def get_api_url(self, environment: Optional[Environment] = None) -> str:
        """Get API URL for environment"""
        if self.config is None:
            self.config = self.load_config()

        env = environment or self.config.environment

        if env == Environment.LOCAL:
            return self.config.api.local_url
        elif env == Environment.STAGING or env == Environment.DEVELOPMENT:
            return self.config.api.staging_url
        else:
            return self.config.api.production_url

    def get_network_config(self, environment: Optional[Environment] = None) -> Dict[str, Any]:
        """Get network configuration for environment"""
        if self.config is None:
            self.config = self.load_config()

        env = environment or self.config.environment

        if env == Environment.LOCAL:
            return {
                "rpc_url": self.config.network.localnet_rpc,
                "chain_id": self.config.network.chain_id_local,
            }
        elif env == Environment.STAGING or env == Environment.DEVELOPMENT:
            return {
                "rpc_url": self.config.network.testnet_rpc,
                "chain_id": self.config.network.chain_id_testnet,
            }
        else:
            return {
                "rpc_url": self.config.network.mainnet_rpc,
                "chain_id": self.config.network.chain_id_mainnet,
            }
