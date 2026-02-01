"""
Deployment Orchestrator - Coordinates complete deployment workflow

This orchestrator coordinates all deployment steps:
1. Project detection (Agent 1)
2. Build execution (Agent 1)
3. Deployment to IPFS (static sites) OR Akash (dynamic apps)
4. Deployment metadata storage
5. App Store submission (optional)
6. Result reporting

HOSTING TYPES:
- Static: Static informational websites (marketing pages, docs, landing pages)
          When listed on App Store: This is the "Website" link
- Dynamic: Dynamic applications with compute (actual apps with frontend + backend)
           When listed on App Store: This is the "Launch App" link

IMPORTANT DISTINCTION:
- Static via Varity Storage = Static site hosting + general file storage
- Dynamic via Varity Compute = Dynamic app hosting with compute resources
"""

import asyncio
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any

from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeElapsedColumn,
)
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

from .types import (
    BuildArtifacts,
    BuildError,
    DeploymentError,
    DeploymentOptions,
    DeploymentResult,
    IPFSUploadError,
    ProjectDetectionError,
    ProjectInfo,
)
from .url_service import VarityURLService
from ..analytics import get_analytics_tracker


class DeploymentOrchestrator:
    """
    Orchestrates complete deployment workflow.

    Coordinates project detection, building, IPFS upload, and metadata storage.

    Usage:
        orchestrator = DeploymentOrchestrator(verbose=True)
        result = orchestrator.deploy(
            project_path=".",
            network="varity",
            submit_to_store=False
        )
        print(f"Deployed to: {result.frontend_url}")
    """

    def __init__(self, verbose: bool = True):
        """
        Initialize deployment orchestrator.

        Args:
            verbose: Whether to print progress messages
        """
        self.verbose = verbose
        self.console = Console()

        # These will be initialized when Agent 1 and Agent 2 are ready
        # For now, we import them lazily to allow testing with mocks
        self._detector = None
        self._builder = None
        self._ipfs = None
        self._akash = None  # Phase 2: Akash deployment (Agent 5)
        self._app_store = None  # Phase 2: App Store client (Agent 6)
        self._history = None  # Phase 2: Deployment history manager (Agent 7)
        self._url_service = VarityURLService()  # URL service for custom domains

        # Progress tracking
        self._start_time = None
        self._stage_timings = {}
        self._progress_callback_ref = None

    @property
    def detector(self):
        """Lazy load ProjectDetector (Agent 1)"""
        if self._detector is None:
            try:
                from .project_detector import ProjectDetector

                self._detector = ProjectDetector()
            except ImportError:
                raise ImportError(
                    "ProjectDetector not yet implemented. " "Waiting for Agent 1 to complete."
                )
        return self._detector

    @property
    def builder(self):
        """Lazy load BuildManager (Agent 1)"""
        if self._builder is None:
            try:
                from .build_manager import BuildManager

                self._builder = BuildManager()
            except ImportError:
                raise ImportError(
                    "BuildManager not yet implemented. " "Waiting for Agent 1 to complete."
                )
        return self._builder

    @property
    def ipfs(self):
        """Lazy load IPFSUploader (Agent 2)"""
        if self._ipfs is None:
            try:
                from .ipfs_uploader import IPFSUploader

                self._ipfs = IPFSUploader()
            except ImportError:
                raise ImportError(
                    "IPFSUploader not yet implemented. " "Waiting for Agent 2 to complete."
                )
        return self._ipfs

    @property
    def akash(self):
        """Lazy load AkashDeployer (Agent 5 - Phase 2)"""
        if self._akash is None:
            try:
                from .akash.akash_deployer import AkashDeployer

                self._akash = AkashDeployer()
            except ImportError:
                raise ImportError(
                    "AkashDeployer not yet implemented. " "Waiting for Agent 5 to complete."
                )
        return self._akash

    @property
    def app_store(self):
        """Lazy load AppStoreClient (Agent 6 - Phase 2)"""
        if self._app_store is None:
            try:
                from .app_store.client import AppStoreClient

                self._app_store = AppStoreClient()
            except ImportError:
                raise ImportError(
                    "AppStoreClient not yet implemented. " "Waiting for Agent 6 to complete."
                )
        return self._app_store

    @property
    def history(self):
        """Lazy load DeploymentHistory (Agent 7 - Phase 2)"""
        if self._history is None:
            from .deployment_history import DeploymentHistory

            self._history = DeploymentHistory()
        return self._history

    def set_progress_callback(self, callback):
        """Set progress callback for deployment updates."""
        self._progress_callback_ref = callback

    def deploy(
        self,
        project_path: str = ".",
        network: str = "varity",
        submit_to_store: bool = False,
        hosting: str = "ipfs",
        akash_resources: Optional[Dict[str, str]] = None,
    ) -> DeploymentResult:
        """
        Deploy application to decentralized infrastructure.

        HOSTING TYPES:
        - ipfs: Static informational websites (marketing pages, docs, landing pages)
                When listed on App Store: This is the "Website" link (uses Varity Storage)
        - akash: Dynamic applications with compute (actual apps with frontend + backend)
                 When listed on App Store: This is the "Launch App" link (uses Varity Compute)

        Args:
            project_path: Path to project directory (default: current directory)
            network: Target network (default: "varity")
            submit_to_store: Auto-submit to App Store
            hosting: Hosting type - "ipfs" (static) or "akash" (dynamic)
            akash_resources: Resource allocation for Akash (cpu, memory, storage)

        Returns:
            DeploymentResult with URLs, CID/deployment info, and manifest

        Raises:
            ProjectDetectionError: If project type cannot be detected
            BuildError: If build fails
            IPFSUploadError: If IPFS upload fails
            DeploymentError: For other deployment failures
        """
        try:
            self._start_time = time.time()
            hosting_type = hosting.lower()

            # Print deployment header
            self.console.print()
            self.console.print(Panel.fit(
                f"[bold cyan]Starting {hosting_type.upper()} Deployment[/bold cyan]",
                border_style="cyan"
            ))
            self.console.print()

            # Step 1: Detect project
            stage_start = time.time()
            with self.console.status("[bold green]Detecting project type...") as status:
                project_info = self._detect_project(project_path)
                elapsed = time.time() - stage_start
                self._stage_timings['detect'] = elapsed

            self.console.print(f"✓ Detected: [cyan]{project_info.project_type}[/cyan] [dim]({elapsed:.1f}s)[/dim]")

            # Step 2: Build project
            build_cmd_display = project_info.build_command or "no build required"
            stage_start = time.time()

            with Progress(
                SpinnerColumn(),
                TextColumn("[bold green]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TimeElapsedColumn(),
                console=self.console,
            ) as progress:
                build_task = progress.add_task(
                    f"Building project ({build_cmd_display})...",
                    total=100
                )

                # Simulate progress updates (in real implementation, builder would call callbacks)
                for i in range(0, 101, 20):
                    progress.update(build_task, completed=i)
                    if i < 100:
                        time.sleep(0.1)  # Remove this in production

                build_artifacts = self._build_project(project_path, project_info)

                if not build_artifacts.success:
                    raise BuildError("Build failed")

                progress.update(build_task, completed=100)

            elapsed = time.time() - stage_start
            self._stage_timings['build'] = elapsed
            self.console.print(
                f"✓ Built {len(build_artifacts.files)} files "
                f"({build_artifacts.total_size_mb:.2f} MB) [dim]({elapsed:.1f}s)[/dim]"
            )
            self.console.print()

            # Step 3: Deploy based on hosting type
            if hosting_type == "ipfs":
                return self._deploy_ipfs(
                    project_info, build_artifacts, project_path, network, submit_to_store
                )
            elif hosting_type == "akash":
                return self._deploy_akash_full(
                    project_info,
                    build_artifacts,
                    project_path,
                    network,
                    submit_to_store,
                    akash_resources or {},
                )
            else:
                raise DeploymentError(f"Unknown hosting type: {hosting_type}")

        except ProjectDetectionError as e:
            self._log(f"❌ Could not detect project type: {e}")
            self._log("   Supported: Next.js, React, Vue")
            self._log("   Ensure package.json exists")
            raise

        except BuildError as e:
            self._log(f"❌ Build failed: {e}")
            self._log("   Try running build manually first")
            raise

        except IPFSUploadError as e:
            self._log(f"❌ Upload failed: {e}")
            self._log("   Check your internet connection")
            raise

        except Exception as e:
            self._log(f"❌ Deployment failed: {e}")
            raise DeploymentError(f"Deployment failed: {e}")

    def _deploy_ipfs(
        self,
        project_info: ProjectInfo,
        build_artifacts: BuildArtifacts,
        project_path: str,
        network: str,
        submit_to_store: bool,
    ) -> DeploymentResult:
        """
        Deploy static site to Varity Storage.

        This is for informational/marketing websites - the "Website" link
        on App Store listings.
        """
        # Upload to Varity Storage
        self._log("☁️  Uploading to Varity Storage...")
        ipfs_result = self._upload_to_ipfs(build_artifacts)

        if not ipfs_result["success"]:
            raise IPFSUploadError(ipfs_result.get("error_message", "Storage upload failed"))

        # Generate custom Varity URLs
        app_name = getattr(project_info, 'package_name', None) or "app"
        varity_url, short_link = self._url_service.generate_urls(
            deployment_id=f"temp-{ipfs_result['cid'][:8]}",  # Temporary ID
            app_name=app_name,
            project_type=project_info.project_type
        )
        varity_url_full = self._url_service.format_url_with_protocol(varity_url)
        short_link_full = self._url_service.format_url_with_protocol(short_link)

        self._log(f"   Deployment ID: {ipfs_result['cid'][:8]}...")
        self._log(f"   Live at: {varity_url_full}")

        # Create deployment manifest
        manifest = self._create_manifest(project_info, build_artifacts, ipfs_result, network)
        manifest["hosting"] = "ipfs"
        manifest["hosting_description"] = "Static informational website"

        # Save deployment metadata
        deployment_id = self._save_deployment(manifest)

        # Submit to App Store if requested
        app_store_url = None
        if submit_to_store:
            app_store_url = self._handle_app_store_submission(
                project_info, ipfs_result["gatewayUrl"], project_path, network, manifest
            )

        # Return result with Varity URLs
        result = DeploymentResult(
            deployment_id=deployment_id,
            frontend_url=varity_url_full,  # Use custom Varity URL instead of IPFS gateway
            manifest=manifest,
            thirdweb_url=short_link_full,  # Use short link
            cid=ipfs_result["cid"],
            app_store_url=app_store_url,
            hosting="ipfs",
        )

        self._log("✅ Static deployment complete!")
        self._log(f"\n   🌐 Static site: {result.frontend_url}")
        self._log(f"   📋 Deployment ID: {result.deployment_id}")
        self._log("   [dim]Note: This is a static site. For dynamic apps, use --hosting akash[/dim]\n")

        # Track deployment analytics (silently fails if analytics unavailable)
        try:
            tracker = get_analytics_tracker()
            tracker.track_deployment(
                app_id=result.deployment_id,
                developer_id=os.getenv('WALLET_ADDRESS', 'unknown'),
                hosting_type='static',
                build_time=build_artifacts.build_time_seconds
            )
            tracker.flush()
        except Exception:
            pass  # Don't fail deployment if analytics fails

        return result

    def _deploy_akash_full(
        self,
        project_info: ProjectInfo,
        build_artifacts: BuildArtifacts,
        project_path: str,
        network: str,
        submit_to_store: bool,
        akash_resources: Dict[str, str],
    ) -> DeploymentResult:
        """
        Deploy dynamic application to Varity Compute.

        This is for actual applications with compute - the "Launch App"
        link on App Store listings.
        """
        # Parse resources
        cpu_units = float(akash_resources.get("cpu", "0.5"))
        memory_size = akash_resources.get("memory", "512Mi")
        storage_size = akash_resources.get("storage", "1Gi")

        self.console.print(f"[bold cyan]Deploying to Varity Compute[/bold cyan]")
        self.console.print(f"Resources: CPU={cpu_units}, Memory={memory_size}, Storage={storage_size}")
        self.console.print()

        try:
            # Import AkashDeploymentConfig
            from .akash.akash_deployer import AkashDeploymentConfig

            # Derive app name from project path
            app_name = Path(project_path).resolve().name

            # Progress tracking
            current_stage = {"name": "", "start": time.time()}
            stage_progress = {}

            # Create progress display
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold]{task.description}"),
                TimeElapsedColumn(),
                console=self.console,
            ) as progress:
                # Create tasks for each deployment stage
                packaging_task = progress.add_task("📦 Packaging source code...", total=None)
                uploading_task = progress.add_task("☁️  Uploading to Varity...", total=None, visible=False)
                building_task = progress.add_task("🏗️  Building application...", total=None, visible=False)
                deploying_task = progress.add_task("🚀 Deploying to Varity Compute...", total=None, visible=False)

                def progress_handler(update):
                    """Handle progress updates from Akash deployer"""
                    if isinstance(update, dict):
                        stage = update.get("stage", "")
                        message = update.get("message", "")
                        elapsed = update.get("elapsed", 0)

                        # Update appropriate task based on stage
                        if "Packaging" in message or "packaging" in message.lower():
                            progress.update(packaging_task, description=f"📦 {message}")
                        elif "Uploading" in message or "upload" in message.lower():
                            progress.update(packaging_task, visible=False)
                            progress.update(uploading_task, visible=True, description=f"☁️  {message}")
                        elif "Building" in message or "build" in message.lower():
                            progress.update(uploading_task, visible=False)
                            progress.update(building_task, visible=True, description=f"🏗️  {message}")
                        elif "Deploying" in message or "deploy" in message.lower() or stage in ["Bidding", "Accepting", "Finalizing"]:
                            progress.update(building_task, visible=False)
                            progress.update(deploying_task, visible=True, description=f"🚀 {message}")

                        # Track stage timing
                        if stage and stage != current_stage["name"]:
                            if current_stage["name"]:
                                stage_progress[current_stage["name"]] = time.time() - current_stage["start"]
                            current_stage["name"] = stage
                            current_stage["start"] = time.time()
                    elif isinstance(update, str):
                        # Legacy string format
                        if "packaging" in update.lower():
                            progress.update(packaging_task, description=f"📦 {update}")
                        elif "upload" in update.lower():
                            progress.update(uploading_task, visible=True, description=f"☁️  {update}")
                        elif "build" in update.lower():
                            progress.update(building_task, visible=True, description=f"🏗️  {update}")
                        else:
                            progress.update(deploying_task, visible=True, description=f"🚀 {update}")

                # Create deployment config
                config = AkashDeploymentConfig(
                    app_name=app_name,
                    path=Path(project_path),  # Send SOURCE CODE, not built output
                    cpu=cpu_units,
                    memory=memory_size,
                    storage=storage_size,
                    env_vars={},
                    progress_callback=progress_handler
                )

                # Deploy to Akash
                akash_result = asyncio.run(self.akash.deploy(config))

            # CHECK SUCCESS FIELD!
            if not akash_result.success:
                error_msg = akash_result.error or "Unknown deployment error"
                self.console.print(f"\n[bold red]❌ Deployment failed:[/bold red] {error_msg}")
                raise DeploymentError(f"Akash deployment failed: {error_msg}")

            # Calculate total time
            total_time = time.time() - self._start_time if self._start_time else 0.0
            self._stage_timings['akash_deploy'] = total_time

            self.console.print(f"\n[bold green]✓ Deployed to Varity Compute![/bold green]")
            self.console.print(f"Deployment ID: [cyan]{akash_result.deployment_id}[/cyan]")

            # Generate custom Varity URLs for Akash deployment
            app_name = getattr(project_info, 'package_name', None) or Path(project_path).name
            varity_url, short_link = self._url_service.generate_urls(
                deployment_id=akash_result.deployment_id,
                app_name=app_name,
                project_type=project_info.project_type
            )
            varity_url_full = self._url_service.format_url_with_protocol(varity_url)
            short_link_full = self._url_service.format_url_with_protocol(short_link)

            if hasattr(akash_result, "provider") and akash_result.provider:
                self.console.print(f"Provider: [cyan]{akash_result.provider}[/cyan]")

            # Create deployment manifest
            manifest = self._create_akash_manifest(
                project_info, build_artifacts, akash_result, network, akash_resources
            )

            # Save deployment metadata
            deployment_id = self._save_deployment(manifest)

            # Submit to App Store if requested
            app_store_url = None
            app_url = akash_result.url if hasattr(akash_result, "url") else None

            if submit_to_store and app_url:
                app_store_url = self._handle_app_store_submission(
                    project_info, app_url, project_path, network, manifest
                )

            # Build result with Akash-specific fields and custom Varity URLs
            result = DeploymentResult(
                deployment_id=deployment_id,
                frontend_url=varity_url_full,  # Use custom Varity URL
                manifest=manifest,
                app_store_url=app_store_url,
                hosting="akash",
                akash_url=varity_url_full,  # Custom URL
                akash_deployment_id=akash_result.deployment_id,
                akash_lease_id=getattr(akash_result, "lease_id", None),
                akash_provider=getattr(akash_result, "provider", None),
                akash_cost=getattr(akash_result, "estimated_cost", None),
            )

            # Print beautiful success summary with custom URLs
            self.console.print()
            summary_text = (
                f"[bold green]✅ Deployment Complete![/bold green]\n\n"
                f"🚀 Live at: [cyan]{varity_url_full}[/cyan]\n"
                f"📋 Deployment ID: [cyan]{result.deployment_id}[/cyan]\n"
                f"⏱️  Total time: [yellow]{total_time:.1f}s[/yellow]\n\n"
                f"[dim]Your app is running on decentralized compute![/dim]"
            )
            self.console.print(Panel.fit(summary_text, border_style="green"))
            self.console.print()

            # Track deployment analytics (silently fails if analytics unavailable)
            try:
                tracker = get_analytics_tracker()
                tracker.track_deployment(
                    app_id=result.deployment_id,
                    developer_id=os.getenv('WALLET_ADDRESS', 'unknown'),
                    hosting_type='dynamic',
                    build_time=build_artifacts.build_time_seconds
                )
                tracker.flush()
            except Exception:
                pass  # Don't fail deployment if analytics fails

            return result

        except Exception as e:
            self._log(f"❌ Dynamic deployment failed: {e}")
            self._log("   Check your internet connection")
            self._log("   Verify project builds locally")
            raise DeploymentError(f"Dynamic deployment failed: {e}")

    def _create_akash_manifest(
        self,
        project_info: ProjectInfo,
        build_artifacts: BuildArtifacts,
        akash_result: Any,
        network: str,
        akash_resources: Dict[str, str],
    ) -> dict:
        """
        Create deployment manifest for Akash deployment.
        """
        now = datetime.now()
        timestamp_microseconds = int(now.timestamp() * 1_000_000)
        deployment_id = f"akash-{timestamp_microseconds}"

        return {
            "version": "1.0",
            "deployment_id": deployment_id,
            "timestamp": datetime.now().isoformat(),
            "network": network,
            "hosting": "akash",
            "hosting_description": "Dynamic application with compute (DePIN)",
            "project": {
                "type": project_info.project_type,
                "framework_version": project_info.framework_version,
                "build_command": project_info.build_command,
                "package_manager": project_info.package_manager,
            },
            "build": {
                "success": build_artifacts.success,
                "files": len(build_artifacts.files),
                "size_mb": build_artifacts.total_size_mb,
                "time_seconds": build_artifacts.build_time_seconds,
                "output_dir": build_artifacts.output_dir,
            },
            "akash": {
                "deployment_id": akash_result.deployment_id,
                "lease_id": getattr(akash_result, "lease_id", None),
                "provider": getattr(akash_result, "provider", None),
                "url": getattr(akash_result, "url", None),
                "cost": getattr(akash_result, "estimated_cost", None),
                "resources": {
                    "cpu": akash_resources.get("cpu", "0.5"),
                    "memory": akash_resources.get("memory", "512Mi"),
                    "storage": akash_resources.get("storage", "1Gi"),
                },
            },
        }

    def _handle_app_store_submission(
        self,
        project_info: ProjectInfo,
        app_url: str,
        project_path: str,
        network: str,
        manifest: dict,
    ) -> Optional[str]:
        """
        Handle App Store submission for both IPFS and Akash deployments.
        """
        self._log("📝 Submitting to App Store...")
        try:
            app_store_result = self._submit_to_app_store(
                project_info,
                {"frontend_url": app_url},
                project_path,
                network,
            )

            if app_store_result and app_store_result.success:
                manifest["app_store"] = {
                    "submitted": True,
                    "app_id": app_store_result.app_id,
                    "tx_hash": app_store_result.tx_hash,
                    "url": app_store_result.url,
                    "status": "pending_approval",
                }
                self._log(f"   ✅ App ID: {app_store_result.app_id}")
                self._log(f"   📱 View at: {app_store_result.url}")
                return app_store_result.url
            else:
                error_msg = (
                    app_store_result.error_message if app_store_result else "Unknown error"
                )
                self._log(f"   ⚠️  App Store submission failed: {error_msg}")
                self._log("   Manual submission: https://store.varity.so/submit")
                manifest["app_store"] = {"submitted": False, "error": error_msg}
                return None
        except Exception as e:
            self._log(f"   ⚠️  App Store submission error: {e}")
            self._log("   Manual submission: https://store.varity.so/submit")
            manifest["app_store"] = {"submitted": False, "error": str(e)}
            return None

    def _detect_project(self, project_path: str) -> ProjectInfo:
        """
        Detect project type using ProjectDetector (Agent 1).

        Args:
            project_path: Path to project directory

        Returns:
            ProjectInfo with detected project details
        """
        return self.detector.detect(project_path)

    def _build_project(self, project_path: str, project_info: ProjectInfo) -> BuildArtifacts:
        """
        Build project using BuildManager (Agent 1).

        Args:
            project_path: Path to project directory
            project_info: Detected project information

        Returns:
            BuildArtifacts with build results
        """
        return self.builder.build(
            project_path=project_path,
            build_command=project_info.build_command,
            output_dir=project_info.output_dir,
        )

    def _upload_to_ipfs(self, build_artifacts: BuildArtifacts) -> dict:
        """
        Upload build artifacts to IPFS using IPFSUploader (Agent 2).

        Args:
            build_artifacts: Build output to upload

        Returns:
            Dictionary with IPFS upload result:
            {
                'success': bool,
                'cid': str,
                'gatewayUrl': str,
                'thirdwebUrl': str,
                'totalSize': int,
                'fileCount': int
            }
        """
        # IPFSUploader.upload() returns IPFSUploadResult object
        # Convert to dict for consistent interface with rest of orchestrator
        result = self.ipfs.upload(build_artifacts.output_dir)
        return {
            "success": result.success,
            "cid": result.cid,
            "gatewayUrl": result.gateway_url,
            "thirdwebUrl": result.thirdweb_url,
            "files": result.files,
            "totalSize": result.total_size,
            "fileCount": result.file_count,
            "uploadTime": result.upload_time,
        }

    def _create_manifest(
        self,
        project_info: ProjectInfo,
        build_artifacts: BuildArtifacts,
        ipfs_result: dict,
        network: str,
    ) -> dict:
        """
        Create deployment manifest.

        Args:
            project_info: Detected project information
            build_artifacts: Build output
            ipfs_result: IPFS upload result
            network: Target network

        Returns:
            Deployment manifest dictionary
        """
        # Use timestamp with microseconds to ensure uniqueness
        now = datetime.now()
        timestamp_microseconds = int(now.timestamp() * 1_000_000)
        deployment_id = f"deploy-{timestamp_microseconds}"

        return {
            "version": "1.0",
            "deployment_id": deployment_id,
            "timestamp": datetime.now().isoformat(),
            "network": network,
            "project": {
                "type": project_info.project_type,
                "framework_version": project_info.framework_version,
                "build_command": project_info.build_command,
                "package_manager": project_info.package_manager,
            },
            "build": {
                "success": build_artifacts.success,
                "files": len(build_artifacts.files),
                "size_mb": build_artifacts.total_size_mb,
                "time_seconds": build_artifacts.build_time_seconds,
                "output_dir": build_artifacts.output_dir,
            },
            "ipfs": {
                "cid": ipfs_result["cid"],
                "gateway_url": ipfs_result["gatewayUrl"],
                "thirdweb_url": ipfs_result["thirdwebUrl"],
                "total_size": ipfs_result.get("totalSize", 0),
                "file_count": ipfs_result.get("fileCount", 0),
            },
        }

    def _save_deployment(self, manifest: dict) -> str:
        """
        Save deployment metadata locally.

        Args:
            manifest: Deployment manifest dictionary

        Returns:
            Deployment ID
        """
        # Create deployments directory
        deployments_dir = Path.home() / ".varitykit" / "deployments"
        deployments_dir.mkdir(parents=True, exist_ok=True)

        deployment_id = manifest["deployment_id"]
        filepath = deployments_dir / f"{deployment_id}.json"

        # Save manifest to file
        with open(filepath, "w") as f:
            json.dump(manifest, f, indent=2)

        self._log(f"   Saved deployment metadata to: {filepath}")

        return deployment_id

    def get_deployment(self, deployment_id: str) -> Optional[dict]:
        """
        Retrieve deployment manifest by ID.

        Args:
            deployment_id: Deployment ID to retrieve

        Returns:
            Deployment manifest dictionary or None if not found
        """
        deployments_dir = Path.home() / ".varitykit" / "deployments"
        filepath = deployments_dir / f"{deployment_id}.json"

        if not filepath.exists():
            return None

        with open(filepath, "r") as f:
            return json.load(f)

    def list_deployments(self, network: Optional[str] = None) -> list:
        """
        List all deployments.

        Args:
            network: Filter by network (optional)

        Returns:
            List of deployment manifest dictionaries
        """
        deployments_dir = Path.home() / ".varitykit" / "deployments"

        if not deployments_dir.exists():
            return []

        deployments = []
        for filepath in deployments_dir.glob("deploy-*.json"):
            with open(filepath, "r") as f:
                manifest = json.load(f)

                # Filter by network if specified
                if network is None or manifest.get("network") == network:
                    deployments.append(manifest)

        # Sort by timestamp (newest first)
        deployments.sort(key=lambda x: x["timestamp"], reverse=True)

        return deployments

    def _submit_to_app_store(
        self, project_info: ProjectInfo, deployment_result: dict, project_path: str, network: str
    ):
        """
        Submit app to Varity App Store (Phase 2 - Agent 6).

        Args:
            project_info: Detected project information
            deployment_result: Deployment result with frontend_url
            project_path: Path to project directory
            network: Target network

        Returns:
            SubmissionResult or None if submission fails
        """
        try:
            from .app_store.metadata_builder import MetadataBuilder

            # Determine chain ID from network
            chain_id_map = {
                "varity": 33529,
                "arbitrum": 42161,
                "arbitrum-sepolia": 421614,
                "base": 8453,
                "base-sepolia": 84532,
            }
            chain_id = chain_id_map.get(network, 33529)

            # Build package.json path
            import os

            package_json_path = os.path.join(project_path, "package.json")

            if not os.path.exists(package_json_path):
                self._log(f"   ⚠️  package.json not found at {package_json_path}")
                return None

            # Build metadata from deployment
            builder = MetadataBuilder()
            metadata = builder.build_from_deployment(
                project_info=project_info,
                deployment_result=deployment_result,
                package_json_path=package_json_path,
                chain_id=chain_id,
            )

            # Submit to App Store contract
            result = self.app_store.submit_app(metadata)

            return result

        except Exception as e:
            self._log(f"   ⚠️  App Store submission error: {e}")
            return None

    def _log(self, message: str):
        """Log message if verbose mode is enabled."""
        if self.verbose:
            print(message)

    def _deploy_to_akash(
        self,
        project_path: str,
        project_info: ProjectInfo,
        build_artifacts: BuildArtifacts,
        deploy_backend: bool = False,
    ):
        """
        Deploy to Akash Network (Phase 2).

        Args:
            project_path: Path to project directory (source code)
            project_info: Detected project information
            build_artifacts: Built artifacts
            deploy_backend: Whether to deploy backend

        Returns:
            AkashDeploymentResult

        Raises:
            DeploymentError: If Akash deployment fails
        """
        from .akash.types import AkashError
        from .akash.akash_deployer import AkashDeploymentConfig

        try:
            # Derive app name from project path
            app_name = Path(project_path).resolve().name

            # Create deployment config
            config = AkashDeploymentConfig(
                app_name=app_name,
                path=Path(project_path),  # Send SOURCE CODE, not built output
                cpu=0.5,
                memory="512Mi",
                storage="1Gi",
                env_vars={},
                progress_callback=lambda msg: self._log(f"   {msg}") if self.verbose else None
            )

            # Deploy frontend to Akash
            result = asyncio.run(self.akash.deploy(config))

            # CHECK SUCCESS FIELD!
            if not result.success:
                error_msg = result.error or "Unknown deployment error"
                self._log(f"   ❌ Deployment failed: {error_msg}")
                raise DeploymentError(f"Akash deployment failed: {error_msg}")

            # TODO: Backend deployment support
            if deploy_backend and project_info.has_backend:
                self._log("   ⚠️  Backend deployment not yet implemented")
                self._log("   Deploy backend manually or wait for future update")

            return result

        except AkashError as e:
            raise DeploymentError(f"Akash deployment failed: {e}")
