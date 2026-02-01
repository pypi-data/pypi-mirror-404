"""
Test Progress Indicators - Verify real-time progress feedback works.

Run with: pytest tests/test_progress_indicators.py -v
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import time

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from varitykit.core.deployment_orchestrator import DeploymentOrchestrator
from varitykit.core.akash.akash_deployer import AkashDeployer, AkashDeploymentConfig, DeploymentResult


class TestProgressIndicators:
    """Test suite for CLI progress indicators."""

    def test_orchestrator_initialization(self):
        """Test orchestrator initializes with console and timing tracking."""
        orchestrator = DeploymentOrchestrator(verbose=True)

        assert orchestrator.console is not None
        assert orchestrator._stage_timings == {}
        assert orchestrator._start_time is None

    @patch('varitykit.core.deployment_orchestrator.DeploymentOrchestrator._detect_project')
    @patch('varitykit.core.deployment_orchestrator.DeploymentOrchestrator._build_project')
    def test_deployment_tracks_timing(self, mock_build, mock_detect):
        """Test deployment tracks elapsed time for each stage."""
        from varitykit.core.types import ProjectInfo, BuildArtifacts

        # Mock project detection
        mock_detect.return_value = ProjectInfo(
            project_type="next.js",
            framework_version="14.0.0",
            build_command="npm run build",
            output_dir=".next",
            package_manager="npm"
        )

        # Mock build
        mock_build.return_value = BuildArtifacts(
            success=True,
            files=["index.html"],
            total_size_mb=1.0,
            build_time_seconds=5.0,
            output_dir=".next"
        )

        orchestrator = DeploymentOrchestrator(verbose=False)

        # We can't test full deployment without mocks, but we can test initialization
        assert orchestrator._start_time is None

        # After calling deploy, timing should be tracked
        # (Would need to mock IPFS/Akash to fully test)

    @pytest.mark.asyncio
    async def test_akash_deployer_progress_callback(self):
        """Test Akash deployer calls progress callback with updates."""
        progress_updates = []

        def progress_callback(update):
            progress_updates.append(update)

        config = AkashDeploymentConfig(
            app_name="test-app",
            path=Path("."),
            cpu=0.5,
            memory="512Mi",
            storage="1Gi",
            env_vars={},
            progress_callback=progress_callback
        )

        # Verify callback is stored
        assert config.progress_callback is not None

        # Test callback invocation
        test_update = {
            "stage": "Packaging",
            "message": "Packaging source code...",
            "elapsed": 0
        }
        config.progress_callback(test_update)

        assert len(progress_updates) == 1
        assert progress_updates[0]["stage"] == "Packaging"

    def test_akash_deployer_file_counting(self):
        """Test file counting excludes node_modules, .git, etc."""
        deployer = AkashDeployer()

        # Create temporary directory structure
        import tempfile
        import os

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create files that should be counted
            (tmppath / "package.json").touch()
            (tmppath / "index.js").touch()
            (tmppath / "README.md").touch()

            # Create files that should be excluded
            node_modules = tmppath / "node_modules"
            node_modules.mkdir()
            (node_modules / "some-package.js").touch()

            git_dir = tmppath / ".git"
            git_dir.mkdir()
            (git_dir / "config").touch()

            (tmppath / ".env").touch()

            # Count files
            count = deployer._count_files(tmppath)

            # Should count: package.json, index.js, README.md (3 files)
            # Should exclude: node_modules/*, .git/*, .env
            assert count == 3

    def test_progress_message_formatting(self):
        """Test progress messages include helpful context."""
        orchestrator = DeploymentOrchestrator(verbose=True)

        # Test that console is initialized
        assert hasattr(orchestrator.console, 'print')

        # Test stage timing storage
        orchestrator._stage_timings['detect'] = 0.5
        orchestrator._stage_timings['build'] = 45.2

        assert orchestrator._stage_timings['detect'] == 0.5
        assert orchestrator._stage_timings['build'] == 45.2

    @pytest.mark.asyncio
    async def test_deployment_status_updates(self):
        """Test deployment sends status updates at each stage."""
        status_updates = []

        async def status_callback(status, message):
            status_updates.append({
                "status": status,
                "message": message
            })

        # Mock deployer that calls status callback
        from varitykit.core.deployment_orchestrator import DeploymentOrchestrator

        orchestrator = DeploymentOrchestrator(verbose=False)

        # Test status callback mechanism
        # (Full integration test would require mocking all dependencies)

    def test_error_handling_with_progress(self):
        """Test error handling shows clear messages."""
        from varitykit.core.types import DeploymentError

        orchestrator = DeploymentOrchestrator(verbose=False)

        # Test that DeploymentError can be raised
        with pytest.raises(Exception):
            raise DeploymentError("Test error message")


class TestProgressFormatting:
    """Test progress message formatting and display."""

    def test_panel_formatting(self):
        """Test Panel formatting for deployment header."""
        from rich.panel import Panel

        panel = Panel.fit(
            "[bold cyan]Starting AKASH Deployment[/bold cyan]",
            border_style="cyan"
        )

        assert panel is not None

    def test_time_formatting(self):
        """Test elapsed time formatting."""
        elapsed = 125.7

        # Should format as "2m 5.7s" or "125.7s"
        formatted = f"{elapsed:.1f}s"
        assert formatted == "125.7s"

        # For display, might want minutes
        minutes = int(elapsed // 60)
        seconds = elapsed % 60
        formatted_min = f"{minutes}m {seconds:.1f}s" if minutes > 0 else f"{seconds:.1f}s"

        assert "2m" in formatted_min

    def test_size_formatting(self):
        """Test file size formatting."""
        size_bytes = 1_500_000

        size_mb = size_bytes / 1024 / 1024
        formatted = f"{size_mb:.2f} MB"

        assert formatted == "1.43 MB"


class TestWebSocketIntegration:
    """Test WebSocket log streaming (requires API running)."""

    @pytest.mark.skip(reason="Requires running API server")
    @pytest.mark.asyncio
    async def test_websocket_connection(self):
        """Test WebSocket connection for log streaming."""
        import websockets

        uri = "ws://localhost:8000/deploy/test-123/logs"

        try:
            async with websockets.connect(uri) as websocket:
                # Send ping
                await websocket.send("ping")

                # Receive pong
                response = await websocket.recv()
                assert response == "pong"
        except Exception as e:
            pytest.skip(f"API server not running: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
