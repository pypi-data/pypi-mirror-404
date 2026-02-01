"""
Deployment History Manager - Manages deployment records and rollback functionality

This module provides functionality to:
1. Save deployment manifests to local storage
2. Retrieve deployment history with filtering
3. Rollback to previous deployments
4. Query deployment status

Storage location: ~/.varitykit/deployments/
Manifest format: v1.0 (Phase 1) and v2.0 (Phase 2)
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .types import DeploymentError, DeploymentResult


class DeploymentHistory:
    """
    Manages deployment history and rollback functionality.

    Stores deployment manifests locally and provides query/rollback capabilities.

    Usage:
        history = DeploymentHistory()

        # Save deployment
        history.save_deployment(result)

        # List deployments
        deployments = history.list_deployments(network='varity', limit=10)

        # Get specific deployment
        deployment = history.get_deployment('deploy-1737492000')

        # Rollback to previous deployment
        new_deployment = history.rollback('deploy-1737492000')
    """

    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize deployment history manager.

        Args:
            storage_path: Custom storage path (default: ~/.varitykit/deployments)
        """
        if storage_path is None:
            self.storage_path = Path.home() / ".varitykit" / "deployments"
        else:
            self.storage_path = Path(storage_path)

        # Ensure storage directory exists
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def save_deployment(
        self,
        result: DeploymentResult,
        project_path: Optional[str] = None,
        deployment_type: str = "ipfs",
        network: str = "varity",
    ) -> None:
        """
        Save deployment manifest to storage.

        Args:
            result: Deployment result to save
            project_path: Path to project directory (optional)
            deployment_type: Type of deployment ('ipfs', 'akash', etc.)
            network: Target network

        Raises:
            DeploymentError: If save fails
        """
        try:
            # Ensure manifest has required fields
            manifest = result.manifest.copy()

            # Add metadata if not present
            if "deployment_id" not in manifest:
                manifest["deployment_id"] = result.deployment_id

            if "timestamp" not in manifest:
                manifest["timestamp"] = datetime.now().isoformat()

            if "network" not in manifest:
                manifest["network"] = network

            # Add project path if provided
            if project_path and "project" in manifest:
                manifest["project"]["path"] = project_path

            # Add deployment type if not present
            if "deployment" not in manifest:
                manifest["deployment"] = {}

            if "type" not in manifest["deployment"]:
                manifest["deployment"]["type"] = deployment_type

            # Save to file
            filepath = self.storage_path / f"{result.deployment_id}.json"

            with open(filepath, "w") as f:
                json.dump(manifest, f, indent=2)

        except Exception as e:
            raise DeploymentError(f"Failed to save deployment: {e}")

    def get_deployment(self, deployment_id: str) -> Optional[Dict[str, Any]]:
        """
        Load deployment manifest by ID.

        Args:
            deployment_id: Deployment ID to retrieve

        Returns:
            Deployment manifest dictionary or None if not found
        """
        filepath = self.storage_path / f"{deployment_id}.json"

        if not filepath.exists():
            return None

        try:
            with open(filepath, "r") as f:
                result = json.load(f)
            return result if isinstance(result, dict) else None
        except Exception:
            return None

    def list_deployments(
        self, network: Optional[str] = None, limit: int = 10, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List deployments with filtering.

        Args:
            network: Filter by network (e.g., 'varity', 'arbitrum')
            limit: Maximum number of deployments to return
            offset: Number of deployments to skip

        Returns:
            List of deployment manifest dictionaries, sorted by timestamp (newest first)
        """
        if not self.storage_path.exists():
            return []

        deployments = []

        # Load all deployment manifests
        for filepath in self.storage_path.glob("deploy-*.json"):
            try:
                with open(filepath, "r") as f:
                    manifest = json.load(f)

                # Filter by network if specified
                if network is None or manifest.get("network") == network:
                    deployments.append(manifest)
            except Exception:
                # Skip corrupted files
                continue

        # Sort by timestamp (newest first)
        deployments.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        # Apply offset and limit
        return deployments[offset : offset + limit]

    def get_latest(self, network: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get the most recent deployment.

        Args:
            network: Filter by network (optional)

        Returns:
            Most recent deployment manifest or None if no deployments found
        """
        deployments = self.list_deployments(network=network, limit=1)
        return deployments[0] if deployments else None

    def rollback(self, deployment_id: str) -> DeploymentResult:
        """
        Rollback to a previous deployment.

        This re-deploys the application using the configuration from the
        specified deployment manifest.

        Args:
            deployment_id: Deployment ID to rollback to

        Returns:
            New DeploymentResult from rollback deployment

        Raises:
            DeploymentError: If deployment not found or rollback fails
        """
        # Load the deployment manifest
        manifest = self.get_deployment(deployment_id)

        if manifest is None:
            raise DeploymentError(
                f"Deployment {deployment_id} not found. "
                f"Available deployments: {self._list_deployment_ids()}"
            )

        # Import orchestrator here to avoid circular imports
        from .deployment_orchestrator import DeploymentOrchestrator

        # Extract deployment parameters from manifest
        network = manifest.get("network", "varity")
        project_path = manifest.get("project", {}).get("path", ".")
        submit_to_store = manifest.get("app_store", {}).get("submitted", False)

        # Create orchestrator and re-deploy
        orchestrator = DeploymentOrchestrator(verbose=True)

        result = orchestrator.deploy(
            project_path=project_path, network=network, submit_to_store=submit_to_store
        )

        return result

    def delete_deployment(self, deployment_id: str) -> bool:
        """
        Delete a deployment manifest.

        Args:
            deployment_id: Deployment ID to delete

        Returns:
            True if deleted, False if not found
        """
        filepath = self.storage_path / f"{deployment_id}.json"

        if not filepath.exists():
            return False

        try:
            filepath.unlink()
            return True
        except Exception:
            return False

    def get_deployment_count(self, network: Optional[str] = None) -> int:
        """
        Get total number of deployments.

        Args:
            network: Filter by network (optional)

        Returns:
            Total deployment count
        """
        return len(self.list_deployments(network=network, limit=10000))

    def _list_deployment_ids(self) -> List[str]:
        """
        Get list of all deployment IDs.

        Returns:
            List of deployment IDs
        """
        deployments = self.list_deployments(limit=10000)
        return [d.get("deployment_id", "") for d in deployments]

    def _format_deployment_summary(self, manifest: Dict[str, Any]) -> str:
        """
        Format deployment manifest into human-readable summary.

        Args:
            manifest: Deployment manifest dictionary

        Returns:
            Formatted summary string
        """
        deployment_id = manifest.get("deployment_id", "unknown")
        timestamp = manifest.get("timestamp", "unknown")
        network = manifest.get("network", "unknown")

        # Extract URLs
        frontend_url = None
        ipfs_cid = None

        if "deployment" in manifest:
            if "frontend" in manifest["deployment"]:
                frontend_url = manifest["deployment"]["frontend"].get("url")
            if "ipfs" in manifest["deployment"]:
                ipfs_cid = manifest["deployment"]["ipfs"].get("cid")
        elif "ipfs" in manifest:
            frontend_url = manifest["ipfs"].get("gateway_url")
            ipfs_cid = manifest["ipfs"].get("cid")

        summary = f"""Deployment: {deployment_id}
Network: {network}
Timestamp: {timestamp}
Frontend URL: {frontend_url or 'N/A'}
IPFS CID: {ipfs_cid or 'N/A'}"""

        return summary

    def export_deployment_history(self, output_path: str) -> None:
        """
        Export all deployment history to a JSON file.

        Args:
            output_path: Path to output file

        Raises:
            DeploymentError: If export fails
        """
        try:
            deployments = self.list_deployments(limit=10000)

            with open(output_path, "w") as f:
                json.dump(
                    {
                        "version": "1.0",
                        "exported_at": datetime.now().isoformat(),
                        "deployment_count": len(deployments),
                        "deployments": deployments,
                    },
                    f,
                    indent=2,
                )
        except Exception as e:
            raise DeploymentError(f"Failed to export deployment history: {e}")

    def import_deployment_history(self, input_path: str) -> int:
        """
        Import deployment history from a JSON file.

        Args:
            input_path: Path to input file

        Returns:
            Number of deployments imported

        Raises:
            DeploymentError: If import fails
        """
        try:
            with open(input_path, "r") as f:
                data = json.load(f)

            deployments = data.get("deployments", [])
            imported_count = 0

            for manifest in deployments:
                deployment_id = manifest.get("deployment_id")
                if deployment_id:
                    filepath = self.storage_path / f"{deployment_id}.json"
                    with open(filepath, "w") as f:
                        json.dump(manifest, f, indent=2)
                    imported_count += 1

            return imported_count
        except Exception as e:
            raise DeploymentError(f"Failed to import deployment history: {e}")
