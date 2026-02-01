"""
Centralized error handling for Varity CLI.

This module provides clear, actionable error messages for web2 developers
who may be unfamiliar with blockchain/decentralized infrastructure.

Error Format:
    - Error Title: What went wrong (concise)
    - Explanation: Why it happened (context)
    - Steps to Fix: Actionable commands/instructions
    - Documentation: Link for more help

Example:
    raise BuildError.missing_lockfile("npm")

    Output:
    Build Failed: Missing package-lock.json

    Your project uses npm but is missing a package-lock.json file.
    This is required for reproducible builds.

    To fix:
      1. Run: npm install
      2. Commit the generated package-lock.json
      3. Try deploying again: varitykit deploy

    Need help? https://docs.varity.so/errors/missing-lockfile
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class ErrorCode(str, Enum):
    """Error codes for categorization and documentation linking."""

    # Build errors (BUILD_xxx)
    BUILD_MISSING_LOCKFILE = "BUILD_001"
    BUILD_COMMAND_NOT_FOUND = "BUILD_002"
    BUILD_FAILED = "BUILD_003"
    BUILD_MISSING_DEPENDENCIES = "BUILD_004"
    BUILD_OUTPUT_NOT_FOUND = "BUILD_005"
    BUILD_EMPTY_OUTPUT = "BUILD_006"

    # Project errors (PROJECT_xxx)
    PROJECT_PATH_NOT_FOUND = "PROJECT_001"
    PROJECT_NO_PACKAGE_JSON = "PROJECT_002"
    PROJECT_INVALID_PACKAGE_JSON = "PROJECT_003"
    PROJECT_UNSUPPORTED_FRAMEWORK = "PROJECT_004"
    PROJECT_DETECTION_FAILED = "PROJECT_005"

    # Network errors (NETWORK_xxx)
    NETWORK_UNREACHABLE = "NETWORK_001"
    NETWORK_TIMEOUT = "NETWORK_002"
    NETWORK_API_ERROR = "NETWORK_003"
    NETWORK_RPC_ERROR = "NETWORK_004"

    # Authentication errors (AUTH_xxx)
    AUTH_MISSING_API_KEY = "AUTH_001"
    AUTH_INVALID_API_KEY = "AUTH_002"
    AUTH_MISSING_CREDENTIALS = "AUTH_003"
    AUTH_EXPIRED_TOKEN = "AUTH_004"

    # IPFS errors (IPFS_xxx)
    IPFS_NODE_NOT_INSTALLED = "IPFS_001"
    IPFS_MISSING_CLIENT_ID = "IPFS_002"
    IPFS_UPLOAD_FAILED = "IPFS_003"
    IPFS_UPLOAD_TIMEOUT = "IPFS_004"
    IPFS_SCRIPT_NOT_FOUND = "IPFS_005"

    # Akash errors (AKASH_xxx)
    AKASH_API_UNREACHABLE = "AKASH_001"
    AKASH_INSUFFICIENT_FUNDS = "AKASH_002"
    AKASH_NO_PROVIDERS = "AKASH_003"
    AKASH_DEPLOYMENT_TIMEOUT = "AKASH_004"
    AKASH_DEPLOYMENT_FAILED = "AKASH_005"
    AKASH_INVALID_CONFIG = "AKASH_006"

    # Config errors (CONFIG_xxx)
    CONFIG_FILE_NOT_FOUND = "CONFIG_001"
    CONFIG_INVALID_FORMAT = "CONFIG_002"
    CONFIG_MISSING_REQUIRED = "CONFIG_003"

    # Generic errors
    UNKNOWN_ERROR = "ERR_000"


# Documentation base URL
DOCS_BASE_URL = "https://docs.varity.so/errors"


@dataclass
class VarityError(Exception):
    """
    Base class for all Varity CLI errors.

    Provides structured error information that can be displayed
    in a user-friendly format with actionable steps.
    """

    title: str
    explanation: str
    fix_steps: List[str] = field(default_factory=list)
    code: ErrorCode = ErrorCode.UNKNOWN_ERROR
    docs_path: str = ""
    details: Optional[str] = None

    def __post_init__(self):
        """Initialize the exception with the title as message."""
        super().__init__(self.title)

    @property
    def docs_url(self) -> str:
        """Get the full documentation URL for this error."""
        if self.docs_path:
            return f"{DOCS_BASE_URL}/{self.docs_path}"
        # Default to error code as path
        return f"{DOCS_BASE_URL}/{self.code.value.lower().replace('_', '-')}"

    def format_message(self, verbose: bool = False) -> str:
        """
        Format the error message for display.

        Args:
            verbose: Include additional technical details

        Returns:
            Formatted error message string
        """
        lines = []

        # Error title
        lines.append(f"\n{self.title}")
        lines.append("")

        # Explanation
        lines.append(self.explanation)
        lines.append("")

        # Fix steps
        if self.fix_steps:
            lines.append("To fix:")
            for i, step in enumerate(self.fix_steps, 1):
                lines.append(f"  {i}. {step}")
            lines.append("")

        # Technical details (verbose mode)
        if verbose and self.details:
            lines.append("Technical details:")
            lines.append(f"  {self.details}")
            lines.append("")

        # Documentation link
        lines.append(f"Need help? {self.docs_url}")
        lines.append(f"Error code: {self.code.value}")
        lines.append("")

        return "\n".join(lines)

    def __str__(self) -> str:
        """Return a concise string representation."""
        return self.format_message(verbose=False)

    def to_dict(self) -> dict:
        """Convert error to dictionary for JSON output."""
        return {
            "error": True,
            "code": self.code.value,
            "title": self.title,
            "explanation": self.explanation,
            "fix_steps": self.fix_steps,
            "docs_url": self.docs_url,
            "details": self.details,
        }


# =============================================================================
# Build Errors
# =============================================================================

class BuildError(VarityError):
    """Errors related to project building."""

    @classmethod
    def missing_lockfile(cls, package_manager: str = "npm") -> "BuildError":
        """Project is missing a lockfile (package-lock.json, yarn.lock, etc.)."""
        lockfile_names = {
            "npm": "package-lock.json",
            "yarn": "yarn.lock",
            "pnpm": "pnpm-lock.yaml",
        }
        lockfile = lockfile_names.get(package_manager, "package-lock.json")

        return cls(
            title=f"Build Failed: Missing {lockfile}",
            explanation=(
                f"Your project uses {package_manager} but is missing a {lockfile} file.\n"
                "This file is required for reproducible builds and ensures all developers\n"
                "and deployment environments use the exact same dependency versions."
            ),
            fix_steps=[
                f"Run: {package_manager} install",
                f"Commit the generated {lockfile} to your repository",
                "Try deploying again: varitykit app deploy",
            ],
            code=ErrorCode.BUILD_MISSING_LOCKFILE,
            docs_path="build/missing-lockfile",
        )

    @classmethod
    def command_not_found(cls, command: str, package_manager: str = "npm") -> "BuildError":
        """Build command (npm, yarn, pnpm) was not found."""
        install_instructions = {
            "npm": "Install Node.js from https://nodejs.org/ (includes npm)",
            "yarn": "Run: npm install -g yarn",
            "pnpm": "Run: npm install -g pnpm",
            "node": "Install Node.js from https://nodejs.org/",
        }

        # Determine what's missing
        if command.startswith("npm") or command.startswith("npx"):
            missing = "npm"
        elif command.startswith("yarn"):
            missing = "yarn"
        elif command.startswith("pnpm"):
            missing = "pnpm"
        else:
            missing = command.split()[0] if command else "node"

        return cls(
            title=f"Build Failed: '{missing}' command not found",
            explanation=(
                f"The build command requires {missing}, but it's not installed\n"
                f"or not in your system PATH.\n\n"
                f"Attempted command: {command}"
            ),
            fix_steps=[
                install_instructions.get(missing, f"Install {missing}"),
                "Restart your terminal after installation",
                f"Verify installation: {missing} --version",
                "Try deploying again: varitykit app deploy",
            ],
            code=ErrorCode.BUILD_COMMAND_NOT_FOUND,
            docs_path="build/command-not-found",
        )

    @classmethod
    def failed_with_exit_code(
        cls,
        exit_code: int,
        command: str,
        output: Optional[str] = None
    ) -> "BuildError":
        """Build command failed with non-zero exit code."""
        # Common exit code explanations
        exit_explanations = {
            1: "General error - check the build output above for details",
            2: "Misuse of shell command or missing file",
            126: "Permission denied - command cannot be executed",
            127: "Command not found in PATH",
            128: "Invalid exit argument",
            130: "Script terminated by Ctrl+C",
            137: "Process killed (possibly out of memory)",
            139: "Segmentation fault",
        }

        explanation = exit_explanations.get(
            exit_code,
            "Unknown error - check the build output above for details"
        )

        fix_steps = [
            "Run the build command manually to see full error output:",
            f"  {command}",
            "Fix any errors shown in the output",
            "Ensure all dependencies are installed: npm install",
            "Try deploying again: varitykit app deploy",
        ]

        # Add memory-specific advice for OOM
        if exit_code == 137:
            fix_steps.insert(2, "If out of memory, try: NODE_OPTIONS='--max-old-space-size=4096' npm run build")

        return cls(
            title=f"Build Failed: Exit code {exit_code}",
            explanation=(
                f"The build command failed with exit code {exit_code}.\n\n"
                f"Explanation: {explanation}\n\n"
                f"Command: {command}"
            ),
            fix_steps=fix_steps,
            code=ErrorCode.BUILD_FAILED,
            docs_path="build/build-failed",
            details=output[:500] if output else None,
        )

    @classmethod
    def output_not_found(cls, expected_dir: str, alternatives: List[str]) -> "BuildError":
        """Build output directory was not found."""
        alternatives_str = ", ".join(alternatives) if alternatives else "none"

        return cls(
            title=f"Build Failed: Output directory not found",
            explanation=(
                f"After building, the expected output directory was not found.\n\n"
                f"Expected: {expected_dir}\n"
                f"Also checked: {alternatives_str}\n\n"
                "This usually means the build failed silently or your project\n"
                "uses a different output directory than expected."
            ),
            fix_steps=[
                "Run the build command manually: npm run build",
                "Check which directory contains the built files",
                "If using a custom output directory, configure it in next.config.js (Next.js)",
                "For React/Vite projects, check vite.config.js for 'outDir' setting",
                "Try deploying again: varitykit app deploy",
            ],
            code=ErrorCode.BUILD_OUTPUT_NOT_FOUND,
            docs_path="build/output-not-found",
        )

    @classmethod
    def empty_output(cls, output_dir: str) -> "BuildError":
        """Build output directory exists but is empty."""
        return cls(
            title="Build Failed: Output directory is empty",
            explanation=(
                f"The build output directory exists but contains no files.\n\n"
                f"Directory: {output_dir}\n\n"
                "This usually means the build failed without raising an error,\n"
                "or the build process didn't generate any output files."
            ),
            fix_steps=[
                "Run the build command manually: npm run build",
                "Check for any warnings or errors in the output",
                "Verify your project has source files to build",
                "Check package.json has a valid 'build' script",
                "Try deploying again: varitykit app deploy",
            ],
            code=ErrorCode.BUILD_EMPTY_OUTPUT,
            docs_path="build/empty-output",
        )


# =============================================================================
# Project Detection Errors
# =============================================================================

class ProjectError(VarityError):
    """Errors related to project detection and validation."""

    @classmethod
    def path_not_found(cls, path: str) -> "ProjectError":
        """Project path does not exist."""
        return cls(
            title="Project Not Found: Path does not exist",
            explanation=(
                f"The specified project path does not exist.\n\n"
                f"Path: {path}\n\n"
                "Make sure you're in the correct directory or specify\n"
                "the correct path with --path."
            ),
            fix_steps=[
                "Check you're in the correct directory: pwd",
                "Verify the path exists: ls -la",
                "Specify the correct path: varitykit app deploy --path /path/to/project",
            ],
            code=ErrorCode.PROJECT_PATH_NOT_FOUND,
            docs_path="project/path-not-found",
        )

    @classmethod
    def no_package_json(cls, path: str) -> "ProjectError":
        """No package.json found in project directory."""
        return cls(
            title="Project Error: No package.json found",
            explanation=(
                f"Could not find package.json in the project directory.\n\n"
                f"Path: {path}\n\n"
                "A package.json file is required for JavaScript/TypeScript projects.\n"
                "For static HTML sites, make sure you have an index.html file."
            ),
            fix_steps=[
                "If this is a new project, run: npm init -y",
                "If deploying a subdirectory, specify it: varitykit app deploy --path ./my-app",
                "For static HTML sites, ensure index.html exists in the root",
            ],
            code=ErrorCode.PROJECT_NO_PACKAGE_JSON,
            docs_path="project/no-package-json",
        )

    @classmethod
    def invalid_package_json(cls, path: str, error: str) -> "ProjectError":
        """package.json exists but is invalid."""
        return cls(
            title="Project Error: Invalid package.json",
            explanation=(
                f"The package.json file exists but could not be parsed.\n\n"
                f"Path: {path}\n"
                f"Error: {error}\n\n"
                "This usually means the JSON syntax is invalid."
            ),
            fix_steps=[
                "Check package.json for syntax errors (missing commas, quotes, etc.)",
                "Validate JSON at https://jsonlint.com/",
                "If the file is corrupted, restore from git: git checkout package.json",
            ],
            code=ErrorCode.PROJECT_INVALID_PACKAGE_JSON,
            docs_path="project/invalid-package-json",
        )

    @classmethod
    def unsupported_framework(cls, dependencies: List[str]) -> "ProjectError":
        """Project uses an unsupported framework."""
        deps_str = ", ".join(dependencies[:10])
        if len(dependencies) > 10:
            deps_str += f"... (+{len(dependencies) - 10} more)"

        return cls(
            title="Project Error: Unsupported framework",
            explanation=(
                f"Could not detect a supported framework in your project.\n\n"
                f"Found dependencies: {deps_str}\n\n"
                "Supported frameworks:\n"
                "  - Next.js (with 'next' dependency)\n"
                "  - React (with 'react' or 'react-scripts')\n"
                "  - Vue.js (with 'vue')\n"
                "  - Node.js backends (with 'express' or 'fastify')\n"
                "  - Static HTML (with index.html, no package.json)"
            ),
            fix_steps=[
                "Ensure your project uses a supported framework",
                "For custom frameworks, create a Dockerfile for Akash deployment",
                "Contact support if you need help: hello@varity.so",
            ],
            code=ErrorCode.PROJECT_UNSUPPORTED_FRAMEWORK,
            docs_path="project/unsupported-framework",
        )


# =============================================================================
# IPFS Upload Errors
# =============================================================================

class IPFSError(VarityError):
    """Errors related to IPFS uploads via thirdweb Storage."""

    @classmethod
    def node_not_installed(cls) -> "IPFSError":
        """Node.js is not installed."""
        return cls(
            title="IPFS Upload Failed: Node.js not installed",
            explanation=(
                "IPFS uploads require Node.js 18 or higher, but Node.js\n"
                "was not found on your system.\n\n"
                "Node.js is needed to run the thirdweb Storage SDK which\n"
                "handles the actual upload to IPFS."
            ),
            fix_steps=[
                "Install Node.js from https://nodejs.org/ (LTS version recommended)",
                "Restart your terminal after installation",
                "Verify installation: node --version",
                "Try deploying again: varitykit app deploy",
            ],
            code=ErrorCode.IPFS_NODE_NOT_INSTALLED,
            docs_path="ipfs/node-not-installed",
        )

    @classmethod
    def upload_timeout(cls, timeout_seconds: int = 300) -> "IPFSError":
        """IPFS upload timed out."""
        return cls(
            title="IPFS Upload Failed: Timeout",
            explanation=(
                f"The upload to IPFS timed out after {timeout_seconds // 60} minutes.\n\n"
                "This can happen with:\n"
                "  - Large file uploads\n"
                "  - Slow or unstable internet connections\n"
                "  - IPFS network congestion"
            ),
            fix_steps=[
                "Check your internet connection",
                "Try uploading a smaller build (remove unnecessary files)",
                "Add large assets to .gitignore and host separately",
                "Try again later if IPFS network is congested",
            ],
            code=ErrorCode.IPFS_UPLOAD_TIMEOUT,
            docs_path="ipfs/upload-timeout",
        )

    @classmethod
    def upload_failed(cls, error: str) -> "IPFSError":
        """IPFS upload failed with an error."""
        return cls(
            title="IPFS Upload Failed",
            explanation=(
                f"The upload to IPFS failed.\n\n"
                f"Error: {error}\n\n"
                "This could be due to network issues, invalid files,\n"
                "or thirdweb Storage service problems."
            ),
            fix_steps=[
                "Check your internet connection",
                "Verify THIRDWEB_CLIENT_ID is set (or use default dev credentials)",
                "Check for invalid file names (special characters, very long names)",
                "Try running: varitykit doctor",
            ],
            code=ErrorCode.IPFS_UPLOAD_FAILED,
            docs_path="ipfs/upload-failed",
            details=error,
        )

    @classmethod
    def script_not_found(cls, script_path: str) -> "IPFSError":
        """IPFS upload script not found."""
        return cls(
            title="IPFS Upload Failed: Upload script missing",
            explanation=(
                f"The IPFS upload script was not found.\n\n"
                f"Expected at: {script_path}\n\n"
                "This usually means the CLI installation is incomplete\n"
                "or corrupted."
            ),
            fix_steps=[
                "Reinstall varitykit: pip install --upgrade varitykit",
                "If installed from source, run: cd cli/scripts && npm install",
                "Try running: varitykit doctor",
            ],
            code=ErrorCode.IPFS_SCRIPT_NOT_FOUND,
            docs_path="ipfs/script-not-found",
        )


# =============================================================================
# Akash Deployment Errors
# =============================================================================

class AkashError(VarityError):
    """Errors related to Akash (DePIN) deployments."""

    @classmethod
    def api_unreachable(cls, api_url: str, error: str) -> "AkashError":
        """Varity Deploy API is unreachable."""
        return cls(
            title="Akash Deployment Failed: API unreachable",
            explanation=(
                f"Could not connect to the Varity Deploy API.\n\n"
                f"API URL: {api_url}\n"
                f"Error: {error}\n\n"
                "This could be due to:\n"
                "  - Network connectivity issues\n"
                "  - API service temporarily unavailable\n"
                "  - Firewall blocking the connection"
            ),
            fix_steps=[
                "Check your internet connection",
                "Try again in a few minutes",
                "Check Varity status at https://status.varity.so",
                "Contact support if the issue persists: hello@varity.so",
            ],
            code=ErrorCode.AKASH_API_UNREACHABLE,
            docs_path="akash/api-unreachable",
            details=error,
        )

    @classmethod
    def insufficient_funds(cls, required: str = "unknown", available: str = "unknown") -> "AkashError":
        """Insufficient AKT tokens for deployment."""
        return cls(
            title="Akash Deployment Failed: Insufficient funds",
            explanation=(
                "You don't have enough AKT tokens to pay for this deployment.\n\n"
                f"Required: {required}\n"
                f"Available: {available}\n\n"
                "Akash deployments require AKT tokens to pay providers for\n"
                "compute resources (CPU, memory, storage)."
            ),
            fix_steps=[
                "Get AKT tokens from an exchange (Osmosis, Kraken, etc.)",
                "Transfer AKT to your deployment wallet",
                "Or use smaller resource allocation: --cpu 0.25 --memory 256Mi",
                "Check current balance: varitykit fund balance",
            ],
            code=ErrorCode.AKASH_INSUFFICIENT_FUNDS,
            docs_path="akash/insufficient-funds",
        )

    @classmethod
    def no_providers(cls) -> "AkashError":
        """No Akash providers available for the deployment."""
        return cls(
            title="Akash Deployment Failed: No providers available",
            explanation=(
                "No Akash providers are currently available to accept your deployment.\n\n"
                "This can happen when:\n"
                "  - Requested resources are too high\n"
                "  - All providers are at capacity\n"
                "  - Network congestion"
            ),
            fix_steps=[
                "Try with smaller resource allocation:",
                "  varitykit app deploy --hosting akash --cpu 0.5 --memory 512Mi",
                "Wait a few minutes and try again",
                "Try during off-peak hours",
            ],
            code=ErrorCode.AKASH_NO_PROVIDERS,
            docs_path="akash/no-providers",
        )

    @classmethod
    def deployment_timeout(cls, timeout_minutes: int = 10) -> "AkashError":
        """Akash deployment timed out."""
        return cls(
            title="Akash Deployment Failed: Timeout",
            explanation=(
                f"The deployment timed out after {timeout_minutes} minutes.\n\n"
                "The deployment may still be in progress on the Akash network.\n"
                "This can happen with complex builds or during high demand."
            ),
            fix_steps=[
                "Check deployment status: varitykit app list",
                "The deployment may complete successfully after the timeout",
                "If stuck, try deploying again",
                "Simplify your build process if timeouts persist",
            ],
            code=ErrorCode.AKASH_DEPLOYMENT_TIMEOUT,
            docs_path="akash/deployment-timeout",
        )

    @classmethod
    def deployment_failed(cls, stage: str, error: str) -> "AkashError":
        """Akash deployment failed at a specific stage."""
        stage_explanations = {
            "packaging": "Failed to package your source code",
            "uploading": "Failed to upload your code to the deploy API",
            "building": "Failed to build Docker image from your code",
            "deploying": "Failed to create deployment on Akash",
            "bidding": "No providers bid on your deployment",
            "accepting": "Failed to accept a provider bid",
            "finalizing": "Failed to finalize the deployment",
        }

        stage_tips = {
            "building": [
                "Ensure your project builds locally: npm run build",
                "Check for missing dependencies",
                "Verify your project has a valid package.json",
            ],
            "deploying": [
                "Try with smaller resources: --cpu 0.5 --memory 512Mi",
                "Wait a few minutes and try again",
            ],
            "bidding": [
                "Try with smaller resources",
                "Try during off-peak hours",
            ],
        }

        explanation = stage_explanations.get(stage, f"Failed at stage: {stage}")
        tips = stage_tips.get(stage, [])

        return cls(
            title=f"Akash Deployment Failed: {stage.capitalize()} error",
            explanation=(
                f"{explanation}\n\n"
                f"Error: {error}"
            ),
            fix_steps=[
                *tips,
                "Check detailed logs: varitykit app list",
                "Try deploying again: varitykit app deploy --hosting akash",
            ],
            code=ErrorCode.AKASH_DEPLOYMENT_FAILED,
            docs_path=f"akash/{stage}-failed",
            details=error,
        )


# =============================================================================
# Network/API Errors
# =============================================================================

class NetworkError(VarityError):
    """Errors related to network connectivity and API calls."""

    @classmethod
    def unreachable(cls, url: str, error: str) -> "NetworkError":
        """Network endpoint is unreachable."""
        return cls(
            title="Network Error: Service unreachable",
            explanation=(
                f"Could not connect to the service.\n\n"
                f"URL: {url}\n"
                f"Error: {error}\n\n"
                "This is usually a temporary network issue."
            ),
            fix_steps=[
                "Check your internet connection",
                "Try again in a few moments",
                "If using a VPN, try disabling it temporarily",
                "Check service status at https://status.varity.so",
            ],
            code=ErrorCode.NETWORK_UNREACHABLE,
            docs_path="network/unreachable",
            details=error,
        )

    @classmethod
    def timeout(cls, operation: str, timeout_seconds: int) -> "NetworkError":
        """Network operation timed out."""
        return cls(
            title=f"Network Error: {operation} timed out",
            explanation=(
                f"The {operation} operation timed out after {timeout_seconds} seconds.\n\n"
                "This could be due to:\n"
                "  - Slow internet connection\n"
                "  - Server under heavy load\n"
                "  - Network congestion"
            ),
            fix_steps=[
                "Check your internet connection",
                "Try again in a few moments",
                "If the issue persists, try during off-peak hours",
            ],
            code=ErrorCode.NETWORK_TIMEOUT,
            docs_path="network/timeout",
        )


# =============================================================================
# Authentication Errors
# =============================================================================

class AuthError(VarityError):
    """Errors related to authentication and credentials."""

    @classmethod
    def missing_api_key(cls, env_var: str = "VARITY_API_KEY") -> "AuthError":
        """Required API key is missing."""
        return cls(
            title="Authentication Error: API key required",
            explanation=(
                f"This operation requires an API key, but {env_var}\n"
                "environment variable is not set.\n\n"
                "API keys authenticate your requests and enable\n"
                "deployment tracking and billing."
            ),
            fix_steps=[
                "Get an API key from https://console.varity.so",
                f"Set the environment variable: export {env_var}=your-api-key",
                "Or add to your shell profile (.bashrc, .zshrc) for persistence",
                "Try the operation again",
            ],
            code=ErrorCode.AUTH_MISSING_API_KEY,
            docs_path="auth/missing-api-key",
        )

    @classmethod
    def invalid_api_key(cls) -> "AuthError":
        """API key is invalid or expired."""
        return cls(
            title="Authentication Error: Invalid API key",
            explanation=(
                "The provided API key is invalid or has expired.\n\n"
                "This could happen if:\n"
                "  - The API key was typed incorrectly\n"
                "  - The API key has been revoked\n"
                "  - The API key has expired"
            ),
            fix_steps=[
                "Verify your API key at https://console.varity.so",
                "Generate a new API key if needed",
                "Update your environment variable with the new key",
            ],
            code=ErrorCode.AUTH_INVALID_API_KEY,
            docs_path="auth/invalid-api-key",
        )


# =============================================================================
# Configuration Errors
# =============================================================================

class ConfigError(VarityError):
    """Errors related to configuration files."""

    @classmethod
    def file_not_found(cls, path: str) -> "ConfigError":
        """Configuration file not found."""
        return cls(
            title="Configuration Error: Config file not found",
            explanation=(
                f"Could not find configuration file.\n\n"
                f"Path: {path}\n\n"
                "A configuration file is optional but helps store\n"
                "project-specific settings."
            ),
            fix_steps=[
                "Initialize a new config: varitykit init",
                "Or specify a different config: --config /path/to/config",
            ],
            code=ErrorCode.CONFIG_FILE_NOT_FOUND,
            docs_path="config/file-not-found",
        )

    @classmethod
    def invalid_format(cls, path: str, error: str) -> "ConfigError":
        """Configuration file has invalid format."""
        return cls(
            title="Configuration Error: Invalid config format",
            explanation=(
                f"The configuration file has an invalid format.\n\n"
                f"Path: {path}\n"
                f"Error: {error}\n\n"
                "Configuration files use TOML format."
            ),
            fix_steps=[
                "Check the config file for syntax errors",
                "Validate TOML at https://www.toml-lint.com/",
                "Delete and reinitialize: rm .varitykit.toml && varitykit init",
            ],
            code=ErrorCode.CONFIG_INVALID_FORMAT,
            docs_path="config/invalid-format",
            details=error,
        )


# =============================================================================
# Helper Functions
# =============================================================================

def format_error_for_rich(error: VarityError, verbose: bool = False) -> str:
    """
    Format a VarityError for Rich console output.

    Returns a string that can be used with Rich Panel for beautiful display.
    """
    lines = []

    # Title (will be styled separately)
    lines.append(f"[bold red]{error.title}[/bold red]")
    lines.append("")

    # Explanation
    lines.append(error.explanation)
    lines.append("")

    # Fix steps
    if error.fix_steps:
        lines.append("[bold cyan]To fix:[/bold cyan]")
        for i, step in enumerate(error.fix_steps, 1):
            lines.append(f"  {i}. [white]{step}[/white]")
        lines.append("")

    # Technical details (verbose mode)
    if verbose and error.details:
        lines.append("[dim]Technical details:[/dim]")
        lines.append(f"[dim]  {error.details[:500]}[/dim]")
        lines.append("")

    # Documentation link
    lines.append(f"[blue]Need help?[/blue] {error.docs_url}")
    lines.append(f"[dim]Error code: {error.code.value}[/dim]")

    return "\n".join(lines)
