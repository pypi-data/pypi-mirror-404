"""
Core modules for VarityKit
"""

# Phase 2: App Store integration (Agent 6)
from varitykit.core.app_store import (
    AppMetadata,
    AppStatus,
    AppStoreClient,
    AppStoreError,
    ContractInteractionError,
    MetadataBuilder,
    MetadataValidationError,
    SubmissionResult,
)
from varitykit.core.build_manager import BuildManager
from varitykit.core.config import ConfigManager, VarityConfig
from varitykit.core.deployment_orchestrator import DeploymentOrchestrator
from varitykit.core.project_detector import ProjectDetector
from varitykit.core.templates import TemplateManager
from varitykit.core.types import (
    BuildArtifacts,
    BuildError,
    DeploymentError,
    DeploymentOptions,
    DeploymentResult,
    IPFSUploadError,
    ProjectDetectionError,
    ProjectInfo,
)

__all__ = [
    "VarityConfig",
    "ConfigManager",
    "TemplateManager",
    "ProjectDetector",
    "BuildManager",
    "DeploymentOrchestrator",
    "ProjectInfo",
    "BuildArtifacts",
    "DeploymentResult",
    "DeploymentOptions",
    "DeploymentError",
    "ProjectDetectionError",
    "BuildError",
    "IPFSUploadError",
    # App Store integration
    "AppStoreClient",
    "MetadataBuilder",
    "AppMetadata",
    "SubmissionResult",
    "AppStatus",
    "AppStoreError",
    "ContractInteractionError",
    "MetadataValidationError",
]
