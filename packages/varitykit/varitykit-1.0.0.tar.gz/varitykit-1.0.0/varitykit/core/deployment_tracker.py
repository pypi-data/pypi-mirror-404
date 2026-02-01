"""
Deployment Tracker Module
Tracks deployment progress across all services (contracts, Akash, Filecoin, Celestia)
"""

import json
import logging
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from web3 import Web3

from .sdk_config import SDKConfig

logger = logging.getLogger(__name__)


class DeploymentStatus(Enum):
    """Deployment status enumeration"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ServiceStatus:
    """Status of a deployment service"""

    name: str
    status: DeploymentStatus
    progress: int  # 0-100
    details: Dict[str, Any]
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    error: Optional[str] = None


@dataclass
class DeploymentState:
    """Complete deployment state"""

    deployment_id: str
    network: str
    customer_id: str
    industry: str
    template_version: str
    services: Dict[str, ServiceStatus]
    overall_status: DeploymentStatus
    overall_progress: int
    started_at: float
    completed_at: Optional[float] = None
    metadata: Dict[str, Any] = None


class DeploymentTracker:
    """
    Tracks deployment status across all services

    Monitors contract deployments, Akash deployments, Filecoin uploads,
    and Celestia DA submissions to provide real-time deployment progress.
    """

    def __init__(self, deployment_id: str, network: str = "testnet"):
        """
        Initialize deployment tracker

        Args:
            deployment_id: Unique deployment identifier
            network: Target network
        """
        self.deployment_id = deployment_id
        self.network = network
        self.config = SDKConfig(network)
        self.blockchain_config = self.config.get_blockchain_config()

        # Initialize Web3 for contract checks
        self.w3 = Web3(Web3.HTTPProvider(self.blockchain_config.rpc_url))

        # State file location
        self.state_dir = Path.home() / ".varitykit" / "deployments" / network
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = self.state_dir / f"{deployment_id}.json"

        # Load or create state
        self.state = self._load_or_create_state()

        logger.info(f"DeploymentTracker initialized for {deployment_id}")

    def _load_or_create_state(self) -> DeploymentState:
        """Load existing state or create new deployment state"""
        if self.state_file.exists():
            with open(self.state_file, "r") as f:
                data = json.load(f)

            # Convert string statuses back to enums
            for service_name, service_data in data["services"].items():
                service_data["status"] = DeploymentStatus(service_data["status"])

            data["overall_status"] = DeploymentStatus(data["overall_status"])

            # Reconstruct ServiceStatus objects
            services = {}
            for name, svc_data in data["services"].items():
                services[name] = ServiceStatus(**svc_data)

            data["services"] = services

            return DeploymentState(**data)
        else:
            # Create new state
            return DeploymentState(
                deployment_id=self.deployment_id,
                network=self.network,
                customer_id="",
                industry="",
                template_version="",
                services={
                    "contracts": ServiceStatus(
                        name="Smart Contracts",
                        status=DeploymentStatus.PENDING,
                        progress=0,
                        details={},
                    ),
                    "akash": ServiceStatus(
                        name="Akash Compute",
                        status=DeploymentStatus.PENDING,
                        progress=0,
                        details={},
                    ),
                    "filecoin": ServiceStatus(
                        name="Filecoin Storage",
                        status=DeploymentStatus.PENDING,
                        progress=0,
                        details={},
                    ),
                    "celestia": ServiceStatus(
                        name="Celestia DA", status=DeploymentStatus.PENDING, progress=0, details={}
                    ),
                },
                overall_status=DeploymentStatus.PENDING,
                overall_progress=0,
                started_at=time.time(),
                metadata={},
            )

    def _save_state(self):
        """Save current state to file"""
        # Convert to dictionary
        data = asdict(self.state)

        # Convert enums to strings
        data["overall_status"] = self.state.overall_status.value
        for service_name in data["services"]:
            data["services"][service_name]["status"] = self.state.services[
                service_name
            ].status.value

        with open(self.state_file, "w") as f:
            json.dump(data, f, indent=2)

    def update_service_status(
        self,
        service: str,
        status: DeploymentStatus,
        progress: int,
        details: Optional[Dict] = None,
        error: Optional[str] = None,
    ):
        """
        Update status of a service

        Args:
            service: Service name (contracts, akash, filecoin, celestia)
            status: New status
            progress: Progress percentage (0-100)
            details: Additional details
            error: Error message if failed
        """
        if service not in self.state.services:
            logger.warning(f"Unknown service: {service}")
            return

        svc = self.state.services[service]

        # Update status
        if svc.status == DeploymentStatus.PENDING and status != DeploymentStatus.PENDING:
            svc.started_at = time.time()

        svc.status = status
        svc.progress = min(100, max(0, progress))

        if details:
            svc.details.update(details)

        if error:
            svc.error = error

        if status == DeploymentStatus.COMPLETED:
            svc.completed_at = time.time()
            svc.progress = 100

        # Update overall progress
        self._update_overall_status()

        # Save state
        self._save_state()

        logger.info(f"{service} status updated: {status.value} ({progress}%)")

    def _update_overall_status(self):
        """Update overall deployment status based on services"""
        services = list(self.state.services.values())

        # Calculate overall progress (average of all services)
        total_progress = sum(s.progress for s in services)
        self.state.overall_progress = total_progress // len(services)

        # Determine overall status
        if any(s.status == DeploymentStatus.FAILED for s in services):
            self.state.overall_status = DeploymentStatus.FAILED
        elif all(s.status == DeploymentStatus.COMPLETED for s in services):
            self.state.overall_status = DeploymentStatus.COMPLETED
            if not self.state.completed_at:
                self.state.completed_at = time.time()
        elif any(s.status == DeploymentStatus.IN_PROGRESS for s in services):
            self.state.overall_status = DeploymentStatus.IN_PROGRESS
        else:
            self.state.overall_status = DeploymentStatus.PENDING

    async def check_contract_deployment(self, contract_address: str) -> bool:
        """
        Check if contract is deployed on blockchain

        Args:
            contract_address: Contract address to check

        Returns:
            True if contract code exists, False otherwise
        """
        try:
            if not self.w3.is_connected():
                logger.warning("Web3 not connected, cannot verify contract")
                return False

            code = self.w3.eth.get_code(contract_address)
            is_deployed = len(code) > 0

            logger.debug(f"Contract {contract_address}: deployed={is_deployed}")

            return is_deployed

        except Exception as e:
            logger.error(f"Failed to check contract deployment: {e}")
            return False

    async def check_akash_deployment(self, deployment_id: str) -> Dict:
        """
        Check Akash deployment status

        Args:
            deployment_id: Akash deployment ID

        Returns:
            Deployment status information
        """
        akash_config = self.config.get_akash_config()

        try:
            # Query Akash API for deployment status
            # This is a placeholder - actual implementation would query Akash RPC
            response = {"deployment_id": deployment_id, "status": "active", "is_running": True}

            logger.debug(f"Akash deployment {deployment_id}: {response}")

            return response

        except Exception as e:
            logger.error(f"Failed to check Akash deployment: {e}")
            return {"status": "unknown", "is_running": False}

    async def check_filecoin_upload(self, cid: str) -> Dict:
        """
        Check if file is available on Filecoin/IPFS

        Args:
            cid: IPFS CID to check

        Returns:
            Upload status information
        """
        filecoin_config = self.config.get_filecoin_config()

        try:
            # Check if CID is accessible via gateway
            gateway_url = f"{filecoin_config.pinata_gateway}/ipfs/{cid}"

            response = requests.head(gateway_url, timeout=10)
            is_available = response.status_code == 200

            logger.debug(f"Filecoin CID {cid}: available={is_available}")

            return {
                "cid": cid,
                "available": is_available,
                "gateway_url": gateway_url if is_available else None,
            }

        except Exception as e:
            logger.error(f"Failed to check Filecoin upload: {e}")
            return {"cid": cid, "available": False}

    async def check_celestia_submission(self, height: int, namespace: str) -> Dict:
        """
        Check Celestia DA submission

        Args:
            height: Block height
            namespace: Celestia namespace

        Returns:
            Submission status information
        """
        celestia_config = self.config.get_celestia_config()

        try:
            # Query Celestia node for data availability
            # This is a placeholder - actual implementation would query Celestia RPC
            response = {"height": height, "namespace": namespace, "available": True}

            logger.debug(f"Celestia submission at height {height}: {response}")

            return response

        except Exception as e:
            logger.error(f"Failed to check Celestia submission: {e}")
            return {"height": height, "available": False}

    def get_deployment_progress(self) -> Dict:
        """
        Get current deployment progress

        Returns:
            Dictionary with deployment progress information
        """
        return {
            "deployment_id": self.deployment_id,
            "network": self.network,
            "overall_status": self.state.overall_status.value,
            "overall_progress": self.state.overall_progress,
            "services": {
                name: {
                    "status": svc.status.value,
                    "progress": svc.progress,
                    "details": svc.details,
                    "error": svc.error,
                }
                for name, svc in self.state.services.items()
            },
            "started_at": self.state.started_at,
            "completed_at": self.state.completed_at,
            "elapsed_time": time.time() - self.state.started_at,
        }

    def get_summary(self) -> str:
        """
        Get human-readable deployment summary

        Returns:
            Formatted summary string
        """
        lines = [
            f"Deployment: {self.deployment_id}",
            f"Network: {self.network}",
            f"Status: {self.state.overall_status.value}",
            f"Progress: {self.state.overall_progress}%",
            "",
            "Services:",
        ]

        for name, svc in self.state.services.items():
            status_icon = {
                DeploymentStatus.PENDING: "⏸️",
                DeploymentStatus.IN_PROGRESS: "🔄",
                DeploymentStatus.COMPLETED: "✅",
                DeploymentStatus.FAILED: "❌",
            }.get(svc.status, "❓")

            lines.append(f"  {status_icon} {svc.name}: {svc.progress}%")

            if svc.error:
                lines.append(f"     Error: {svc.error}")

        elapsed = time.time() - self.state.started_at
        lines.append(f"\nElapsed Time: {elapsed:.1f}s")

        return "\n".join(lines)

    @staticmethod
    def list_deployments(network: str) -> List[str]:
        """
        List all deployments for a network

        Args:
            network: Network to list deployments for

        Returns:
            List of deployment IDs
        """
        state_dir = Path.home() / ".varitykit" / "deployments" / network

        if not state_dir.exists():
            return []

        deployment_ids = [f.stem for f in state_dir.glob("*.json")]
        return sorted(deployment_ids, reverse=True)  # Most recent first
