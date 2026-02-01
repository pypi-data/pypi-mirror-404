"""
Contract Verifier Module
Verifies deployed contracts on Arbiscan block explorer
"""

import logging
import time
from dataclasses import dataclass
from typing import Dict, Optional

import requests

from .sdk_config import SDKConfig

logger = logging.getLogger(__name__)


@dataclass
class VerificationResult:
    """Contract verification result"""

    contract_address: str
    contract_name: str
    verified: bool
    verification_url: Optional[str] = None
    error: Optional[str] = None
    guid: Optional[str] = None


class ContractVerifier:
    """
    Verifies smart contracts on Arbiscan block explorer

    Submits contract source code and constructor arguments
    to Arbiscan API for verification.
    """

    def __init__(self, network: str = "testnet", api_key: Optional[str] = None):
        """
        Initialize contract verifier

        Args:
            network: Target network
            api_key: Arbiscan API key (from environment if not provided)
        """
        self.network = network
        self.config = SDKConfig(network)
        self.blockchain_config = self.config.get_blockchain_config()

        # Get API key
        import os

        self.api_key = api_key or os.getenv("ARBISCAN_API_KEY", "")

        # Set API endpoint based on network
        if self.blockchain_config.is_testnet:
            self.api_base = "https://api-sepolia.arbiscan.io/api"
        else:
            self.api_base = "https://api.arbiscan.io/api"

        logger.info(f"ContractVerifier initialized for {network}")

    def verify_contract(
        self,
        contract_address: str,
        contract_name: str,
        source_code: str,
        compiler_version: str,
        constructor_args: str = "",
        optimization_used: bool = True,
        runs: int = 200,
        evm_version: str = "default",
    ) -> VerificationResult:
        """
        Verify contract on Arbiscan

        Args:
            contract_address: Deployed contract address
            contract_name: Name of the contract
            source_code: Solidity source code
            compiler_version: Solidity compiler version (e.g., 'v0.8.22+commit.4fc1097e')
            constructor_args: ABI-encoded constructor arguments (hex string)
            optimization_used: Whether optimization was enabled
            runs: Number of optimization runs
            evm_version: EVM version (e.g., 'paris', 'london', 'default')

        Returns:
            Verification result
        """
        if not self.api_key:
            logger.warning("No Arbiscan API key provided, skipping verification")
            return VerificationResult(
                contract_address=contract_address,
                contract_name=contract_name,
                verified=False,
                error="No API key provided",
            )

        try:
            logger.info(f"Verifying contract {contract_name} at {contract_address}...")

            # Prepare verification request
            params = {
                "module": "contract",
                "action": "verifysourcecode",
                "apikey": self.api_key,
                "contractaddress": contract_address,
                "sourceCode": source_code,
                "codeformat": "solidity-single-file",
                "contractname": contract_name,
                "compilerversion": compiler_version,
                "optimizationUsed": "1" if optimization_used else "0",
                "runs": str(runs),
                "constructorArguements": constructor_args.replace("0x", ""),
                "evmversion": evm_version,
                "licenseType": "3",  # MIT License
            }

            # Submit verification
            response = requests.post(self.api_base, data=params, timeout=30)
            response.raise_for_status()

            result = response.json()

            if result["status"] == "1":
                # Verification submitted successfully
                guid = result["result"]
                logger.info(f"Verification submitted: GUID={guid}")

                # Wait for verification to complete
                verified = self._wait_for_verification(guid, timeout=180)

                if verified:
                    verification_url = (
                        f"{self.blockchain_config.explorer_url}/address/{contract_address}#code"
                    )

                    logger.info(f"Contract verified successfully: {verification_url}")

                    return VerificationResult(
                        contract_address=contract_address,
                        contract_name=contract_name,
                        verified=True,
                        verification_url=verification_url,
                        guid=guid,
                    )
                else:
                    return VerificationResult(
                        contract_address=contract_address,
                        contract_name=contract_name,
                        verified=False,
                        error="Verification timeout or failed",
                        guid=guid,
                    )
            else:
                error_msg = result.get("result", "Unknown error")
                logger.error(f"Verification submission failed: {error_msg}")

                return VerificationResult(
                    contract_address=contract_address,
                    contract_name=contract_name,
                    verified=False,
                    error=error_msg,
                )

        except requests.RequestException as e:
            logger.error(f"Verification request failed: {e}")
            return VerificationResult(
                contract_address=contract_address,
                contract_name=contract_name,
                verified=False,
                error=str(e),
            )

    def _wait_for_verification(self, guid: str, timeout: int = 180) -> bool:
        """
        Wait for verification to complete

        Args:
            guid: Verification GUID from Arbiscan
            timeout: Maximum time to wait (seconds)

        Returns:
            True if verified, False otherwise
        """
        start_time = time.time()
        check_interval = 5  # seconds

        while time.time() - start_time < timeout:
            try:
                # Check verification status
                params = {
                    "module": "contract",
                    "action": "checkverifystatus",
                    "apikey": self.api_key,
                    "guid": guid,
                }

                response = requests.get(self.api_base, params=params, timeout=10)
                response.raise_for_status()

                result = response.json()

                if result["status"] == "1":
                    # Verification completed successfully
                    logger.info(f'Verification completed: {result["result"]}')
                    return True

                elif result["result"] == "Pending in queue":
                    # Still pending, wait and retry
                    logger.debug(f"Verification pending... ({int(time.time() - start_time)}s)")
                    time.sleep(check_interval)

                else:
                    # Verification failed
                    logger.error(f'Verification failed: {result["result"]}')
                    return False

            except requests.RequestException as e:
                logger.warning(f"Failed to check verification status: {e}")
                time.sleep(check_interval)

        logger.warning(f"Verification timeout after {timeout}s")
        return False

    def check_verification_status(self, contract_address: str) -> bool:
        """
        Check if contract is already verified

        Args:
            contract_address: Contract address to check

        Returns:
            True if verified, False otherwise
        """
        try:
            params = {
                "module": "contract",
                "action": "getsourcecode",
                "address": contract_address,
                "apikey": self.api_key,
            }

            response = requests.get(self.api_base, params=params, timeout=10)
            response.raise_for_status()

            result = response.json()

            if result["status"] == "1" and len(result["result"]) > 0:
                source_code = result["result"][0].get("SourceCode", "")
                return len(source_code) > 0

            return False

        except requests.RequestException as e:
            logger.error(f"Failed to check verification status: {e}")
            return False

    def get_verification_url(self, contract_address: str) -> str:
        """
        Get verification URL for contract

        Args:
            contract_address: Contract address

        Returns:
            Block explorer URL with verification info
        """
        return f"{self.blockchain_config.explorer_url}/address/{contract_address}#code"

    def verify_multiple_contracts(
        self, contracts: Dict[str, Dict]
    ) -> Dict[str, VerificationResult]:
        """
        Verify multiple contracts

        Args:
            contracts: Dictionary mapping contract names to verification params
                      Each contract should have: address, source_code, compiler_version

        Returns:
            Dictionary mapping contract names to verification results
        """
        results = {}

        for contract_name, params in contracts.items():
            result = self.verify_contract(
                contract_address=params["address"],
                contract_name=contract_name,
                source_code=params["source_code"],
                compiler_version=params["compiler_version"],
                constructor_args=params.get("constructor_args", ""),
                optimization_used=params.get("optimization_used", True),
                runs=params.get("runs", 200),
                evm_version=params.get("evm_version", "default"),
            )

            results[contract_name] = result

            # Rate limiting: wait between submissions
            if len(contracts) > 1:
                time.sleep(2)

        return results
