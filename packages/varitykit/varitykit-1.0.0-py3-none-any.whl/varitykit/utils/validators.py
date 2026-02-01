"""
Validation utilities for VarityKit CLI
"""

import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


@dataclass
class ValidationResult:
    """Result of a validation check"""

    passed: bool
    message: str
    details: Optional[str] = None


class EnvironmentValidator:
    """Validates development environment requirements"""

    REQUIRED_TOOLS = {
        "docker": {"min_version": "20.10.0", "command": ["docker", "--version"]},
        "docker-compose": {"min_version": "1.29.0", "command": ["docker-compose", "--version"]},
        "node": {"min_version": "16.0.0", "command": ["node", "--version"]},
        "npm": {"min_version": "8.0.0", "command": ["npm", "--version"]},
        "python": {"min_version": "3.10.0", "command": ["python3", "--version"]},
        "git": {"min_version": "2.0.0", "command": ["git", "--version"]},
    }

    @staticmethod
    def check_tool_installed(tool: str) -> ValidationResult:
        """Check if a tool is installed"""
        if shutil.which(tool) is None and shutil.which(f"{tool}.exe") is None:
            return ValidationResult(
                passed=False,
                message=f"{tool} is not installed",
                details=f"Install {tool} from the official website",
            )
        return ValidationResult(passed=True, message=f"{tool} is installed")

    @staticmethod
    def parse_version(version_string: str) -> Tuple[int, int, int]:
        """Parse version string to tuple of integers"""
        # Extract version numbers using regex
        match = re.search(r"(\d+)\.(\d+)\.(\d+)", version_string)
        if match:
            groups = match.groups()
            return (int(groups[0]), int(groups[1]), int(groups[2]))
        return (0, 0, 0)

    @classmethod
    def check_tool_version(cls, tool: str, config: Dict) -> ValidationResult:
        """Check if tool meets minimum version requirement"""
        try:
            result = subprocess.run(config["command"], capture_output=True, text=True, timeout=5)

            if result.returncode != 0:
                return ValidationResult(
                    passed=False, message=f"Failed to check {tool} version", details=result.stderr
                )

            version_output = result.stdout + result.stderr
            current_version = cls.parse_version(version_output)
            required_version = cls.parse_version(config["min_version"])

            if current_version >= required_version:
                return ValidationResult(
                    passed=True,
                    message=f"{tool} version {'.'.join(map(str, current_version))} meets requirement",
                    details=f"Required: {config['min_version']}",
                )
            else:
                return ValidationResult(
                    passed=False,
                    message=f"{tool} version {'.'.join(map(str, current_version))} is too old",
                    details=f"Required: {config['min_version']}",
                )

        except subprocess.TimeoutExpired:
            return ValidationResult(passed=False, message=f"Timeout checking {tool} version")
        except Exception as e:
            return ValidationResult(passed=False, message=f"Error checking {tool}", details=str(e))

    @classmethod
    def validate_environment(cls) -> Dict[str, ValidationResult]:
        """Validate entire development environment"""
        results = {}

        for tool, config in cls.REQUIRED_TOOLS.items():
            # First check if tool is installed
            install_result = cls.check_tool_installed(tool.split()[0])
            if not install_result.passed:
                results[tool] = install_result
                continue

            # Then check version
            version_result = cls.check_tool_version(tool, config)
            results[tool] = version_result

        return results

    @staticmethod
    def check_docker_running() -> ValidationResult:
        """Check if Docker daemon is running"""
        try:
            result = subprocess.run(["docker", "ps"], capture_output=True, text=True, timeout=5)

            if result.returncode == 0:
                return ValidationResult(passed=True, message="Docker daemon is running")
            else:
                return ValidationResult(
                    passed=False,
                    message="Docker daemon is not running",
                    details="Start Docker Desktop or Docker daemon",
                )

        except Exception as e:
            return ValidationResult(
                passed=False, message="Failed to check Docker status", details=str(e)
            )


class ConfigValidator:
    """Validates configuration files and settings"""

    @staticmethod
    def validate_project_name(name: str) -> ValidationResult:
        """Validate project name format"""
        # Project names should be lowercase with hyphens
        if not re.match(r"^[a-z][a-z0-9-]*[a-z0-9]$", name):
            return ValidationResult(
                passed=False,
                message="Invalid project name",
                details="Project names must start with a letter, contain only lowercase letters, numbers, and hyphens",
            )

        if len(name) < 3:
            return ValidationResult(
                passed=False,
                message="Project name too short",
                details="Project names must be at least 3 characters",
            )

        if len(name) > 50:
            return ValidationResult(
                passed=False,
                message="Project name too long",
                details="Project names must be at most 50 characters",
            )

        return ValidationResult(passed=True, message="Valid project name")

    @staticmethod
    def validate_directory_empty(path: Path) -> ValidationResult:
        """Check if directory is empty or doesn't exist"""
        if not path.exists():
            return ValidationResult(
                passed=True, message="Directory does not exist (will be created)"
            )

        if path.is_file():
            return ValidationResult(
                passed=False, message="Path exists but is a file, not a directory"
            )

        # Check if directory has any files (excluding hidden files)
        contents = list(path.glob("*"))
        if contents:
            return ValidationResult(
                passed=False,
                message="Directory is not empty",
                details=f"Found {len(contents)} items",
            )

        return ValidationResult(passed=True, message="Directory is empty")

    @staticmethod
    def validate_api_key(api_key: str) -> ValidationResult:
        """Validate API key format"""
        if not api_key or len(api_key) < 32:
            return ValidationResult(
                passed=False,
                message="Invalid API key",
                details="API key must be at least 32 characters",
            )

        return ValidationResult(passed=True, message="Valid API key format")

    @staticmethod
    def validate_wallet_address(address: str) -> ValidationResult:
        """Validate Ethereum wallet address"""
        if not re.match(r"^0x[a-fA-F0-9]{40}$", address):
            return ValidationResult(
                passed=False,
                message="Invalid wallet address",
                details="Must be a valid Ethereum address (0x + 40 hex characters)",
            )

        return ValidationResult(passed=True, message="Valid wallet address")


class LocalDePinValidator:
    """Validates LocalDePin network services"""

    LOCALDEPIN_SERVICES = {
        "arbitrum-l3": {"port": 8547, "name": "Arbitrum L3 Node"},
        "ipfs": {"port": 5001, "name": "IPFS Gateway"},
        "pinata-mock": {"port": 3002, "name": "Pinata Mock Service"},
        "akash-simulator": {"port": 8081, "name": "Akash Simulator"},
        "celestia-da": {"port": 26658, "name": "Celestia DA Node"},
        "postgres": {"port": 5432, "name": "PostgreSQL Database"},
        "redis": {"port": 6379, "name": "Redis Cache"},
        "varity-api": {"port": 3001, "name": "Varity API Local"},
        "explorer": {"port": 3000, "name": "VarityKit Explorer"},
    }

    @staticmethod
    def check_service_running(service_name: str, port: int) -> ValidationResult:
        """Check if LocalDePin service is running"""
        import socket

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(2)
                result = sock.connect_ex(("localhost", port))

                if result == 0:
                    return ValidationResult(
                        passed=True, message=f"{service_name} is running on port {port}"
                    )
                else:
                    return ValidationResult(
                        passed=False,
                        message=f"{service_name} is not running",
                        details=f"Port {port} is not accessible",
                    )

        except Exception as e:
            return ValidationResult(
                passed=False, message=f"Error checking {service_name}", details=str(e)
            )

    @classmethod
    def check_all_services(cls) -> Dict[str, ValidationResult]:
        """Check all LocalDePin services"""
        results = {}

        for service_key, config in cls.LOCALDEPIN_SERVICES.items():
            service_name = str(config["name"])
            service_port = int(config["port"]) if isinstance(config["port"], (int, str)) else 0
            results[service_key] = cls.check_service_running(service_name, service_port)

        return results

    @staticmethod
    def check_docker_compose_running() -> ValidationResult:
        """Check if docker-compose services are running"""
        try:
            result = subprocess.run(
                ["docker-compose", "ps", "--services", "--filter", "status=running"],
                capture_output=True,
                text=True,
                timeout=5,
                cwd=Path.cwd(),
            )

            if result.returncode == 0:
                running_services = result.stdout.strip().split("\n")
                running_count = len([s for s in running_services if s])

                if running_count > 0:
                    return ValidationResult(
                        passed=True,
                        message=f"{running_count} services running",
                        details=", ".join(running_services),
                    )
                else:
                    return ValidationResult(
                        passed=False,
                        message="No services running",
                        details="Run 'varitykit localdepin start' to start services",
                    )
            else:
                return ValidationResult(
                    passed=False,
                    message="docker-compose not found in current directory",
                    details="Navigate to a VarityKit project or run 'varitykit init'",
                )

        except Exception as e:
            return ValidationResult(
                passed=False, message="Failed to check docker-compose", details=str(e)
            )


class SystemValidator:
    """Validates system resources and configuration"""

    @staticmethod
    def check_disk_space(min_gb: int = 10) -> ValidationResult:
        """Check available disk space"""
        import shutil

        try:
            total, used, free = shutil.disk_usage("/")
            free_gb = free // (2**30)  # Convert to GB

            if free_gb >= min_gb:
                return ValidationResult(
                    passed=True, message=f"{free_gb}GB available", details=f"Required: {min_gb}GB"
                )
            else:
                return ValidationResult(
                    passed=False,
                    message=f"Low disk space: {free_gb}GB available",
                    details=f"Required: {min_gb}GB",
                )

        except Exception as e:
            return ValidationResult(
                passed=False, message="Failed to check disk space", details=str(e)
            )

    @staticmethod
    def check_memory(min_gb: int = 4) -> ValidationResult:
        """Check available memory"""
        try:
            # Try to get memory info on Linux
            with open("/proc/meminfo", "r") as f:
                meminfo = {}
                for line in f:
                    parts = line.split(":")
                    if len(parts) == 2:
                        key = parts[0].strip()
                        value = parts[1].strip().split()[0]
                        meminfo[key] = int(value)

                available_kb = meminfo.get("MemAvailable", meminfo.get("MemFree", 0))
                available_gb = available_kb // (1024 * 1024)

                if available_gb >= min_gb:
                    return ValidationResult(
                        passed=True,
                        message=f"{available_gb}GB available",
                        details=f"Required: {min_gb}GB",
                    )
                else:
                    return ValidationResult(
                        passed=False,
                        message=f"Low memory: {available_gb}GB available",
                        details=f"Required: {min_gb}GB",
                    )

        except FileNotFoundError:
            # Not on Linux, try alternative methods
            import psutil

            try:
                mem = psutil.virtual_memory()
                available_gb = mem.available // (1024**3)

                if available_gb >= min_gb:
                    return ValidationResult(passed=True, message=f"{available_gb}GB available")
                else:
                    return ValidationResult(
                        passed=False,
                        message=f"Low memory: {available_gb}GB available",
                        details=f"Required: {min_gb}GB",
                    )
            except Exception:
                return ValidationResult(
                    passed=True, message="Memory check skipped (psutil not available)"
                )

        except Exception as e:
            return ValidationResult(passed=False, message="Failed to check memory", details=str(e))

    @staticmethod
    def check_env_file() -> ValidationResult:
        """Check if .env file exists"""
        env_file = Path(".env")

        if env_file.exists():
            return ValidationResult(passed=True, message=".env file found")
        else:
            return ValidationResult(
                passed=False,
                message=".env file not found",
                details="Run 'varitykit init' to create project with .env",
            )

    @staticmethod
    def check_config_file() -> ValidationResult:
        """Check if varity.config.json exists"""
        config_file = Path("varity.config.json")

        if config_file.exists():
            import json

            try:
                with open(config_file, "r") as f:
                    config = json.load(f)

                return ValidationResult(
                    passed=True,
                    message="Configuration file valid",
                    details=f"Industry: {config.get('industry', 'unknown')}",
                )
            except json.JSONDecodeError:
                return ValidationResult(
                    passed=False, message="Configuration file invalid", details="JSON syntax error"
                )
        else:
            return ValidationResult(
                passed=False,
                message="Configuration file not found",
                details="Run 'varitykit init' to create project",
            )


class NetworkValidator:
    """Validates network connectivity and endpoints"""

    @staticmethod
    def check_port_available(port: int) -> ValidationResult:
        """Check if a port is available"""
        import socket

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex(("localhost", port))

                if result == 0:
                    return ValidationResult(
                        passed=False,
                        message=f"Port {port} is already in use",
                        details="Stop the service using this port or choose a different port",
                    )
                else:
                    return ValidationResult(passed=True, message=f"Port {port} is available")

        except Exception as e:
            return ValidationResult(
                passed=False, message=f"Error checking port {port}", details=str(e)
            )

    @staticmethod
    def check_internet_connection() -> ValidationResult:
        """Check internet connectivity"""
        import socket

        try:
            # Try to connect to Google's DNS server
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return ValidationResult(passed=True, message="Internet connection available")
        except OSError:
            return ValidationResult(
                passed=False,
                message="No internet connection",
                details="Check your network settings",
            )

    @staticmethod
    def check_api_endpoint(url: str, timeout: int = 5) -> ValidationResult:
        """Check if API endpoint is accessible"""
        import requests

        try:
            response = requests.get(url, timeout=timeout)

            if response.status_code < 500:
                return ValidationResult(
                    passed=True, message=f"API endpoint accessible (status {response.status_code})"
                )
            else:
                return ValidationResult(
                    passed=False,
                    message=f"API endpoint error (status {response.status_code})",
                    details=response.text[:200],
                )

        except requests.exceptions.Timeout:
            return ValidationResult(
                passed=False,
                message="API endpoint timeout",
                details=f"No response within {timeout} seconds",
            )
        except requests.exceptions.ConnectionError:
            return ValidationResult(
                passed=False,
                message="Cannot connect to API endpoint",
                details="Check URL and network connectivity",
            )
        except Exception as e:
            return ValidationResult(
                passed=False, message="Error checking API endpoint", details=str(e)
            )

    @staticmethod
    def check_blockchain_rpc(rpc_url: str, network_name: str) -> ValidationResult:
        """Check blockchain RPC connectivity"""
        import requests

        try:
            # Standard JSON-RPC request to get chain ID
            payload = {"jsonrpc": "2.0", "method": "eth_chainId", "params": [], "id": 1}

            response = requests.post(rpc_url, json=payload, timeout=5)

            if response.status_code == 200:
                data = response.json()
                if "result" in data:
                    chain_id = (
                        int(data["result"], 16)
                        if isinstance(data["result"], str)
                        else data["result"]
                    )
                    return ValidationResult(
                        passed=True,
                        message=f"{network_name} RPC accessible",
                        details=f"Chain ID: {chain_id}",
                    )
                else:
                    return ValidationResult(
                        passed=False,
                        message=f"{network_name} RPC error",
                        details=data.get("error", {}).get("message", "Unknown error"),
                    )
            else:
                return ValidationResult(
                    passed=False,
                    message=f"{network_name} RPC error (status {response.status_code})",
                )

        except Exception as e:
            return ValidationResult(
                passed=False, message=f"Cannot connect to {network_name} RPC", details=str(e)
            )

    @staticmethod
    def check_ipfs_gateway(gateway_url: str = "http://localhost:5001") -> ValidationResult:
        """Check IPFS gateway connectivity"""
        import requests

        try:
            # Try to access IPFS API version endpoint
            response = requests.post(f"{gateway_url}/api/v0/version", timeout=3)

            if response.status_code == 200:
                data = response.json()
                version = data.get("Version", "unknown")
                return ValidationResult(
                    passed=True, message="IPFS gateway accessible", details=f"Version: {version}"
                )
            else:
                return ValidationResult(
                    passed=False,
                    message="IPFS gateway error",
                    details=f"Status: {response.status_code}",
                )

        except Exception as e:
            return ValidationResult(
                passed=False, message="Cannot connect to IPFS gateway", details=str(e)
            )
