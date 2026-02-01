"""
Data structures for the deployment system.

This module defines the core data types used throughout the deployment
orchestration system.
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ProjectInfo:
    """
    Information about a detected project.

    Attributes:
        project_type: Type of project ('static', 'nextjs', 'react', 'vue', 'nodejs', 'python')
        framework_version: Version of the framework (e.g., '14.0.0')
        build_command: Command to build the project (e.g., 'npm run build')
        output_dir: Directory where build artifacts are created (e.g., './out', './build')
        package_manager: Package manager used ('npm', 'yarn', 'pnpm', None for static)
        has_backend: Whether the project includes a backend (server/ directory)
    """

    project_type: str
    framework_version: Optional[str]
    build_command: str
    output_dir: str
    package_manager: Optional[str]  # None for static HTML sites
    has_backend: bool = False


@dataclass
class BuildArtifacts:
    """
    Output from the build process.

    Attributes:
        success: Whether the build was successful
        output_dir: Directory containing build artifacts
        files: List of file paths relative to output_dir
        entrypoint: Main entrypoint file (e.g., 'index.html' for SPA)
        total_size_mb: Total size of build artifacts in megabytes
        build_time_seconds: Time taken to build in seconds
    """

    success: bool
    output_dir: str
    files: List[str]
    entrypoint: str
    total_size_mb: float
    build_time_seconds: float


@dataclass
class DeploymentOptions:
    """
    Options for deployment configuration.

    Attributes:
        submit_to_store: Whether to submit to App Store after deployment
        deploy_backend: Whether to deploy backend (if exists)
        deployment_method: Deployment method ('ipfs' or 'akash')
    """

    submit_to_store: bool = False
    deploy_backend: bool = True
    deployment_method: str = "ipfs"


@dataclass
class DeploymentResult:
    """
    Complete deployment result.

    Supports two hosting types:
    - IPFS: Static informational websites (marketing pages, docs)
            When listed on App Store: This is the "Website" link
    - Akash: Dynamic applications with compute (actual apps)
             When listed on App Store: This is the "Launch App" link

    IPFS-specific Attributes:
        thirdweb_url: thirdweb CDN URL (faster alternative)
        cid: IPFS Content Identifier (CID)

    Akash-specific Attributes:
        akash_url: Dynamic app URL on Akash
        akash_deployment_id: Akash deployment identifier
        akash_lease_id: Akash lease identifier
        akash_provider: Akash provider address
        akash_cost: Estimated deployment cost

    Common Attributes:
        deployment_id: Unique identifier for this deployment
        frontend_url: App URL (IPFS gateway or Akash URL)
        app_store_url: App Store submission URL (optional)
        manifest: Full deployment manifest dictionary
        hosting: Hosting type ("ipfs" or "akash")
    """

    deployment_id: str
    frontend_url: str
    manifest: dict

    # IPFS-specific fields (optional for Akash deployments)
    thirdweb_url: Optional[str] = None
    cid: Optional[str] = None

    # Akash-specific fields (optional for IPFS deployments)
    akash_url: Optional[str] = None
    akash_deployment_id: Optional[str] = None
    akash_lease_id: Optional[str] = None
    akash_provider: Optional[str] = None
    akash_cost: Optional[str] = None

    # Common optional fields
    app_store_url: Optional[str] = None
    hosting: str = "ipfs"

    def __str__(self):
        """Pretty string representation"""
        if self.hosting == "akash":
            return f"""Deployment {self.deployment_id} (Akash/DePIN)
  App URL: {self.akash_url or self.frontend_url}
  Akash Deployment: {self.akash_deployment_id}
  Provider: {self.akash_provider}
  Hosting: Dynamic app with compute"""
        else:
            return f"""Deployment {self.deployment_id} (IPFS)
  Frontend: {self.frontend_url}
  CID: {self.cid}
  Hosting: Static informational site"""

    @property
    def is_static(self) -> bool:
        """Returns True if this is a static IPFS deployment"""
        return self.hosting == "ipfs"

    @property
    def is_dynamic(self) -> bool:
        """Returns True if this is a dynamic Akash deployment"""
        return self.hosting == "akash"

    @property
    def app_url(self) -> str:
        """Returns the primary app URL regardless of hosting type"""
        if self.hosting == "akash" and self.akash_url:
            return self.akash_url
        return self.frontend_url


# Error classes
class DeploymentError(Exception):
    """Base class for deployment errors"""

    pass


class ProjectDetectionError(DeploymentError):
    """Raised when project type cannot be detected"""

    pass


class BuildError(DeploymentError):
    """Raised when build fails"""

    pass


class IPFSUploadError(DeploymentError):
    """Raised when IPFS upload fails"""

    pass
