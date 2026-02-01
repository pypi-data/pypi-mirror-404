"""
Varity Storage Uploader

Uploads directories to Varity Storage (decentralized storage) via Node.js bridge script.
This module provides a Python interface to the storage SDK.

Provides clear, actionable error messages for web2 developers.
"""

import json
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

from .errors import IPFSError


# Keep backward compatibility
class IPFSUploadError(Exception):
    """Raised when IPFS upload fails (deprecated, use IPFSError instead)"""

    pass


class IPFSUploadResult:
    """Result of an IPFS upload operation"""

    def __init__(self, data: Dict):
        self.success: bool = data.get("success", False)
        self.cid: str = data.get("cid", "")
        self.gateway_url: str = data.get("gatewayUrl", "")
        self.thirdweb_url: str = data.get("thirdwebUrl", "")
        self.files: List[str] = data.get("files", [])
        self.total_size: int = data.get("totalSize", 0)
        self.file_count: int = data.get("fileCount", 0)
        self.upload_time: int = data.get("uploadTime", 0)

    def __repr__(self):
        return (
            f"IPFSUploadResult(cid='{self.cid}', "
            f"files={self.file_count}, "
            f"size={self.total_size} bytes, "
            f"time={self.upload_time}ms)"
        )


class IPFSUploader:
    """
    Upload files to Varity Storage

    This class provides a Python interface to upload directories to
    Varity Storage (decentralized storage). It uses a Node.js bridge script
    to leverage the TypeScript SDK.

    Example:
        uploader = IPFSUploader()
        result = uploader.upload('./build')
        print(f"Uploaded to Varity Storage: {result.gateway_url}")
        print(f"Deployment ID: {result.cid}")
    """

    def __init__(self, client_id: Optional[str] = None):
        """
        Initialize IPFS uploader

        Args:
            client_id: thirdweb client ID (optional, falls back to env var)
        """
        # Priority: explicit arg > env var
        self.client_id = (
            client_id
            or os.getenv("VARITY_THIRDWEB_CLIENT_ID")
            or os.getenv("THIRDWEB_CLIENT_ID")
            or ""
        )

        if not self.client_id:
            raise IPFSError.upload_failed(
                "Thirdweb Client ID required for storage uploads.\n\n"
                "To fix this, either:\n"
                "1. Set VARITY_THIRDWEB_CLIENT_ID environment variable\n"
                "2. Pass client_id parameter to IPFSUploader\n"
                "3. Deploy via Varity (varitykit deploy) for automatic credentials\n\n"
                "Get your Client ID at: https://thirdweb.com/dashboard"
            )
        self.script_path = Path(__file__).parent.parent.parent / "scripts" / "upload_to_ipfs.js"

        # Verify Node.js script exists
        if not self.script_path.exists():
            raise IPFSError.script_not_found(str(self.script_path))

    def upload(self, directory: str) -> IPFSUploadResult:
        """
        Upload directory to Varity Storage

        Uploads all files in the specified directory to Varity Storage
        (decentralized storage). Returns upload result with deployment ID and URLs.

        Args:
            directory: Path to directory to upload

        Returns:
            IPFSUploadResult with deployment ID, URLs, and metadata

        Raises:
            IPFSUploadError: If upload fails
            FileNotFoundError: If directory doesn't exist

        Example:
            uploader = IPFSUploader()
            result = uploader.upload('./out')

            print(f"Success: {result.success}")
            print(f"Deployment ID: {result.cid}")
            print(f"Live URL: {result.gateway_url}")
            print(f"Files uploaded: {result.file_count}")
        """
        # Validate directory exists
        dir_path = Path(directory).resolve()
        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        if not dir_path.is_dir():
            raise ValueError(f"Path is not a directory: {directory}")


        # Check Node.js is installed
        try:
            subprocess.run(["node", "--version"], capture_output=True, check=True, timeout=5)
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise IPFSError.node_not_installed()

        # Build command
        cmd = ["node", str(self.script_path), str(dir_path), self.client_id]

        try:
            # Execute Node.js script
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=300, check=False  # 5 minute timeout
            )

            # Parse JSON output
            if result.returncode == 0:
                # Success - parse stdout
                try:
                    data = json.loads(result.stdout)
                    return IPFSUploadResult(data)
                except json.JSONDecodeError as e:
                    raise IPFSError.upload_failed(
                        f"Failed to parse upload result: {e}\nOutput: {result.stdout}"
                    )
            else:
                # Failure - parse stderr for helpful error message
                error_details = ""
                try:
                    error_data = json.loads(result.stderr)
                    error_msg = error_data.get("error", "Unknown error")
                    error_details = error_msg
                except json.JSONDecodeError:
                    # Stderr is not JSON, use raw error
                    error_details = (
                        f"Return code: {result.returncode}\n"
                        f"Error output: {result.stderr or result.stdout}"
                    )

                # Provide context-specific error messages
                if "THIRDWEB_CLIENT_ID" in error_details or "client" in error_details.lower():
                    raise IPFSError.upload_failed(
                        "Storage credentials may be invalid or expired.\n"
                        f"Details: {error_details}\n\n"
                        "Contact support if this issue persists."
                    )
                elif "network" in error_details.lower() or "connect" in error_details.lower():
                    raise IPFSError.upload_failed(
                        "Network error during upload.\n"
                        "Check your internet connection and try again.\n"
                        f"Details: {error_details}"
                    )
                else:
                    raise IPFSError.upload_failed(error_details)

        except subprocess.TimeoutExpired:
            raise IPFSError.upload_timeout(300)
        except IPFSError:
            # Re-raise our errors as-is
            raise
        except Exception as e:
            raise IPFSError.upload_failed(f"Unexpected error: {str(e)}")

    def check_dependencies(self) -> Dict[str, bool]:
        """
        Check if all dependencies are available

        Returns:
            Dict with status of each dependency

        Example:
            uploader = IPFSUploader()
            status = uploader.check_dependencies()

            if not status['node_installed']:
                print("Please install Node.js")
            if not status['script_exists']:
                print("Run: cd cli/scripts && npm install")
        """
        status = {
            "node_installed": False,
            "script_exists": self.script_path.exists(),
            "client_id_set": bool(self.client_id),
        }

        # Check Node.js
        try:
            result = subprocess.run(["node", "--version"], capture_output=True, timeout=5)
            status["node_installed"] = result.returncode == 0
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        return status

    def get_file_count(self, directory: str) -> int:
        """
        Count files in directory recursively

        Args:
            directory: Path to directory

        Returns:
            Number of files

        Example:
            uploader = IPFSUploader()
            count = uploader.get_file_count('./build')
            print(f"Will upload {count} files")
        """
        dir_path = Path(directory)
        if not dir_path.exists():
            return 0

        return sum(1 for _ in dir_path.rglob("*") if _.is_file())

    def get_directory_size(self, directory: str) -> int:
        """
        Calculate total size of directory in bytes

        Args:
            directory: Path to directory

        Returns:
            Total size in bytes

        Example:
            uploader = IPFSUploader()
            size = uploader.get_directory_size('./build')
            print(f"Directory size: {size / 1024 / 1024:.2f} MB")
        """
        dir_path = Path(directory)
        if not dir_path.exists():
            return 0

        total_size = 0
        for file_path in dir_path.rglob("*"):
            if file_path.is_file():
                total_size += file_path.stat().st_size

        return total_size

    @staticmethod
    def format_size(size_bytes: int) -> str:
        """
        Format byte size as human-readable string

        Args:
            size_bytes: Size in bytes

        Returns:
            Formatted string (e.g., "1.5 MB")

        Example:
            formatted = IPFSUploader.format_size(1500000)
            print(formatted)  # "1.43 MB"
        """
        size: float = float(size_bytes)
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"
