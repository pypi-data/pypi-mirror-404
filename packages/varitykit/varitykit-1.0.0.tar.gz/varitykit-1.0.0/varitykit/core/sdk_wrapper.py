"""
SDK Wrapper - Python bridge to TypeScript Varity SDK
Executes TypeScript SDK methods via subprocess
"""

import json
import logging
import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from .sdk_config import SDKConfig

logger = logging.getLogger(__name__)


@dataclass
class ContractDeploymentResult:
    """Result of contract deployment"""

    address: str
    transaction_hash: str
    block_number: int
    gas_used: int
    contract_name: str


@dataclass
class AkashDeploymentResult:
    """Result of Akash deployment"""

    deployment_id: str
    lease_id: str
    provider: str
    service_url: str
    cost_uakt: int
    created_at: int


@dataclass
class FilecoinUploadResult:
    """Result of Filecoin/IPFS upload"""

    cid: str
    size: int
    layer: str
    encrypted: bool
    timestamp: int


class SDKWrapperError(Exception):
    """SDK Wrapper execution error"""

    pass


class VaritySDKWrapper:
    """
    Python wrapper for TypeScript Varity SDK

    Executes TypeScript code via ts-node subprocess to interact with
    the varity-core-backend SDK package.
    """

    def __init__(self, network: str = "testnet"):
        """
        Initialize SDK wrapper

        Args:
            network: Target network ('local', 'testnet', or 'mainnet')
        """
        self.network = network
        self.config = SDKConfig(network)
        self.sdk_path = self.config.get_sdk_base_path()

        # Verify ts-node is available
        self._verify_ts_node()

        logger.info(f"VaritySDKWrapper initialized for {network}")

    def _verify_ts_node(self):
        """Verify ts-node is installed and available"""
        try:
            result = subprocess.run(
                ["npx", "ts-node", "--version"], capture_output=True, text=True, timeout=10
            )
            if result.returncode != 0:
                raise SDKWrapperError("ts-node not found. Install with: npm install -g ts-node")

            logger.debug(f"ts-node version: {result.stdout.strip()}")

        except subprocess.TimeoutExpired:
            raise SDKWrapperError("ts-node verification timed out")
        except FileNotFoundError:
            raise SDKWrapperError("npx not found. Please install Node.js and npm")

    def _execute_typescript(self, script: str, timeout: int = 300) -> Dict:
        """
        Execute TypeScript code and return JSON output

        Args:
            script: TypeScript code to execute
            timeout: Execution timeout in seconds

        Returns:
            Parsed JSON output from script

        Raises:
            SDKWrapperError: If execution fails
        """
        # Create temporary TypeScript file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".ts", dir=self.sdk_path, delete=False
        ) as f:
            f.write(script)
            script_path = f.name

        try:
            logger.debug(f"Executing TypeScript: {script_path}")

            # Set environment variables
            env = os.environ.copy()
            env.update(
                {
                    "WALLET_PRIVATE_KEY": os.getenv("WALLET_PRIVATE_KEY", ""),
                    "PINATA_API_KEY": os.getenv("PINATA_API_KEY", ""),
                    "PINATA_API_SECRET": os.getenv("PINATA_API_SECRET", ""),
                    "AKASH_WALLET_MNEMONIC": os.getenv("AKASH_WALLET_MNEMONIC", ""),
                    "CELESTIA_AUTH_TOKEN": os.getenv("CELESTIA_AUTH_TOKEN", ""),
                    "ARBISCAN_API_KEY": os.getenv("ARBISCAN_API_KEY", ""),
                }
            )

            # Execute with ts-node
            result = subprocess.run(
                ["npx", "ts-node", script_path],
                cwd=str(self.sdk_path),
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env,
            )

            # Check for errors
            if result.returncode != 0:
                error_msg = result.stderr or result.stdout
                logger.error(f"TypeScript execution failed: {error_msg}")
                raise SDKWrapperError(f"SDK execution failed: {error_msg}")

            # Parse JSON output
            try:
                output: Dict[Any, Any] = json.loads(result.stdout.strip())
                logger.debug(f"TypeScript output: {output}")
                return output
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON output: {result.stdout}")
                raise SDKWrapperError(f"Invalid JSON output: {e}")

        finally:
            # Clean up temporary file
            try:
                os.unlink(script_path)
            except Exception:
                pass

    async def deploy_contracts(
        self, contract_names: List[str]
    ) -> Dict[str, ContractDeploymentResult]:
        """
        Deploy smart contracts to blockchain

        Args:
            contract_names: List of contract names to deploy

        Returns:
            Dictionary mapping contract names to deployment results
        """
        blockchain_config = self.config.get_blockchain_config()

        script = f"""
import {{ ContractManager }} from './src/services/ContractManager';
import {{ ethers }} from 'ethers';

async function deployContracts() {{
  const config = {{
    chainId: {blockchain_config.chain_id},
    name: '{blockchain_config.name}',
    rpcUrl: '{blockchain_config.rpc_url}',
    explorerUrl: '{blockchain_config.explorer_url}',
    isTestnet: {str(blockchain_config.is_testnet).lower()}
  }};

  const manager = new ContractManager(
    config,
    process.env.WALLET_PRIVATE_KEY
  );

  const results = {{}};

  // Deploy each contract
  const contractsToDeploy = {json.dumps(contract_names)};

  for (const contractName of contractsToDeploy) {{
    try {{
      // Load contract ABI and bytecode
      const {{ abi, bytecode }} = require(`./artifacts/${{contractName}}.json`);

      const result = await manager.deployContract(abi, bytecode, []);

      results[contractName] = {{
        address: result.address,
        transactionHash: result.transactionHash,
        blockNumber: result.blockNumber,
        gasUsed: result.gasUsed.toString(),
        contractName: contractName
      }};
    }} catch (error) {{
      results[contractName] = {{
        error: error.message
      }};
    }}
  }}

  console.log(JSON.stringify(results));
}}

deployContracts().catch(error => {{
  console.error(JSON.stringify({{ error: error.message }}));
  process.exit(1);
}});
"""

        result = self._execute_typescript(script, timeout=600)

        # Convert to dataclass instances
        deployments = {}
        for name, data in result.items():
            if "error" in data:
                raise SDKWrapperError(f"Failed to deploy {name}: {data['error']}")

            deployments[name] = ContractDeploymentResult(
                address=data["address"],
                transaction_hash=data["transactionHash"],
                block_number=int(data["blockNumber"]),
                gas_used=int(data["gasUsed"]),
                contract_name=data["contractName"],
            )

        return deployments

    async def deploy_to_akash(
        self,
        image: str,
        cpu_millicores: int,
        memory_mb: int,
        storage_gb: int,
        env_vars: Optional[Dict[str, str]] = None,
        service_name: str = "llm-inference",
    ) -> AkashDeploymentResult:
        """
        Deploy workload to Akash Network

        Args:
            image: Docker image to deploy
            cpu_millicores: CPU allocation in millicores
            memory_mb: Memory allocation in MB
            storage_gb: Storage allocation in GB
            env_vars: Environment variables for deployment
            service_name: Name of the service

        Returns:
            Akash deployment result
        """
        akash_config = self.config.get_akash_config()
        env_vars_json = json.dumps(env_vars or {})

        script = f"""
import {{ AkashClient }} from './src/depin/AkashClient';

async function deployToAkash() {{
  const config = {{
    rpcEndpoint: '{akash_config.rpc_endpoint}',
    chainId: '{akash_config.chain_id}',
    walletMnemonic: process.env.AKASH_WALLET_MNEMONIC || ''
  }};

  const client = new AkashClient(config);

  const spec = {{
    cpu: {cpu_millicores},
    memory: {memory_mb},
    storage: {storage_gb},
    image: '{image}',
    env: {env_vars_json},
    expose: [
      {{
        port: 8080,
        protocol: 'http',
        global: true
      }}
    ]
  }};

  const result = await client.deploy(spec, '{service_name}');

  console.log(JSON.stringify({{
    deploymentId: result.deploymentId,
    leaseId: result.leaseId,
    provider: result.provider,
    serviceUrl: result.services['{service_name}'].uri,
    costUakt: result.cost.amount,
    createdAt: result.createdAt
  }}));
}}

deployToAkash().catch(error => {{
  console.error(JSON.stringify({{ error: error.message }}));
  process.exit(1);
}});
"""

        result = self._execute_typescript(script, timeout=600)

        if "error" in result:
            raise SDKWrapperError(f"Akash deployment failed: {result['error']}")

        return AkashDeploymentResult(
            deployment_id=result["deploymentId"],
            lease_id=result["leaseId"],
            provider=result["provider"],
            service_url=result["serviceUrl"],
            cost_uakt=int(result["costUakt"]),
            created_at=int(result["createdAt"]),
        )

    async def upload_to_filecoin(
        self, file_path: str, layer: str, namespace: str, encrypt: bool = True
    ) -> FilecoinUploadResult:
        """
        Upload file to Filecoin/IPFS with optional encryption

        Args:
            file_path: Path to file to upload
            layer: Storage layer (varity-internal, industry-rag, customer-data)
            namespace: Namespace for the upload
            encrypt: Whether to encrypt with Lit Protocol

        Returns:
            Filecoin upload result with CID
        """
        filecoin_config = self.config.get_filecoin_config()

        # Read file content
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            raise SDKWrapperError(f"File not found: {file_path}")

        script = f"""
import {{ FilecoinClient }} from './src/depin/FilecoinClient';
import {{ readFileSync }} from 'fs';

async function uploadToFilecoin() {{
  const config = {{
    pinataApiKey: process.env.PINATA_API_KEY || '',
    pinataSecretKey: process.env.PINATA_API_SECRET || '',
    gatewayUrl: '{filecoin_config.pinata_gateway}'
  }};

  const client = new FilecoinClient(config);

  // Initialize encryption if needed
  if ({str(encrypt).lower()}) {{
    await client.initializeEncryption();
  }}

  // Read file
  const fileData = readFileSync('{file_path}');

  // Upload to Filecoin
  const result = await client.uploadFile(
    fileData,
    '{layer}',
    {{
      namespace: '{namespace}',
      encrypt: {str(encrypt).lower()}
    }}
  );

  console.log(JSON.stringify({{
    cid: result.cid,
    size: result.size,
    layer: result.layer,
    encrypted: result.encrypted,
    timestamp: result.timestamp
  }}));
}}

uploadToFilecoin().catch(error => {{
  console.error(JSON.stringify({{ error: error.message }}));
  process.exit(1);
}});
"""

        result = self._execute_typescript(script, timeout=300)

        if "error" in result:
            raise SDKWrapperError(f"Filecoin upload failed: {result['error']}")

        return FilecoinUploadResult(
            cid=result["cid"],
            size=int(result["size"]),
            layer=result["layer"],
            encrypted=bool(result["encrypted"]),
            timestamp=int(result["timestamp"]),
        )

    async def register_dashboard(
        self,
        registry_address: str,
        customer_id: str,
        dashboard_url: str,
        industry: str,
        template_version: str,
        storage_cid: str,
    ) -> str:
        """
        Register dashboard on-chain

        Args:
            registry_address: DashboardRegistry contract address
            customer_id: Customer identifier
            dashboard_url: URL of deployed dashboard
            industry: Industry template used
            template_version: Version of template
            storage_cid: IPFS CID of template data

        Returns:
            Transaction hash
        """
        blockchain_config = self.config.get_blockchain_config()

        script = f"""
import {{ ContractManager }} from './src/services/ContractManager';

async function registerDashboard() {{
  const config = {{
    chainId: {blockchain_config.chain_id},
    name: '{blockchain_config.name}',
    rpcUrl: '{blockchain_config.rpc_url}',
    explorerUrl: '{blockchain_config.explorer_url}',
    isTestnet: {str(blockchain_config.is_testnet).lower()}
  }};

  const manager = new ContractManager(
    config,
    process.env.WALLET_PRIVATE_KEY
  );

  // Load DashboardRegistry ABI
  const {{ abi }} = require('./artifacts/DashboardRegistry.json');

  manager.initializeDashboardRegistry('{registry_address}', abi);

  const receipt = await manager.registerDashboard(
    '{customer_id}',
    '{dashboard_url}',
    '{industry}',
    '{template_version}',
    '{storage_cid}'
  );

  console.log(JSON.stringify({{
    transactionHash: receipt.hash,
    blockNumber: receipt.blockNumber
  }}));
}}

registerDashboard().catch(error => {{
  console.error(JSON.stringify({{ error: error.message }}));
  process.exit(1);
}});
"""

        result = self._execute_typescript(script, timeout=180)

        if "error" in result:
            raise SDKWrapperError(f"Dashboard registration failed: {result['error']}")

        tx_hash: str = result["transactionHash"]
        return tx_hash

    async def estimate_gas(self, contract_address: str, method_name: str, args: List[Any]) -> int:
        """
        Estimate gas for a contract method call

        Args:
            contract_address: Contract address
            method_name: Method to call
            args: Method arguments

        Returns:
            Estimated gas units
        """
        blockchain_config = self.config.get_blockchain_config()
        args_json = json.dumps(args)

        script = f"""
import {{ ContractManager }} from './src/services/ContractManager';

async function estimateGas() {{
  const config = {{
    chainId: {blockchain_config.chain_id},
    name: '{blockchain_config.name}',
    rpcUrl: '{blockchain_config.rpc_url}',
    explorerUrl: '{blockchain_config.explorer_url}',
    isTestnet: {str(blockchain_config.is_testnet).lower()}
  }};

  const manager = new ContractManager(config);

  // This would require loading the contract ABI
  // For now, return a mock estimate
  const gasEstimate = 300000;

  console.log(JSON.stringify({{
    gasEstimate: gasEstimate.toString()
  }}));
}}

estimateGas().catch(error => {{
  console.error(JSON.stringify({{ error: error.message }}));
  process.exit(1);
}});
"""

        result = self._execute_typescript(script, timeout=60)

        if "error" in result:
            raise SDKWrapperError(f"Gas estimation failed: {result['error']}")

        return int(result["gasEstimate"])
