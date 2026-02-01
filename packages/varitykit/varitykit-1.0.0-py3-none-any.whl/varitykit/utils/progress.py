"""
Progress indicators and status displays for VarityKit CLI.

Provides Vercel-style progress tracking for long-running operations.

Features:
- Real-time progress bars with spinners
- Stage-based updates with completion marks
- Estimated time remaining (ETA) based on historical data
- Color-coded status messages
"""

from typing import Optional, Callable, Dict, List
import time
import json
from pathlib import Path

from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.console import Console
from rich.text import Text


# Default time estimates for deployment stages (seconds)
DEFAULT_STAGE_ESTIMATES = {
    # IPFS deployment stages
    "analyze": 2,
    "build": 30,
    "upload": 15,
    # Akash deployment stages
    "packaging": 5,
    "uploading": 10,
    "building": 45,
    "deploying": 20,
    "bidding": 15,
    "accepting": 5,
    "finalizing": 10,
}

# Path for storing historical deployment times
HISTORY_FILE = Path.home() / ".varitykit" / "deployment_times.json"


class DeploymentTimeTracker:
    """
    Tracks historical deployment times to provide accurate ETAs.

    Maintains a rolling average of deployment times for each stage,
    which improves ETA accuracy as more deployments are performed.
    """

    def __init__(self, max_samples: int = 50):
        """
        Initialize time tracker.

        Args:
            max_samples: Maximum number of samples to keep per stage
        """
        self.max_samples = max_samples
        self.stage_times: Dict[str, List[float]] = {}
        self.estimates: Dict[str, float] = DEFAULT_STAGE_ESTIMATES.copy()
        self._load_history()

    def _load_history(self):
        """Load historical deployment times from disk."""
        try:
            if HISTORY_FILE.exists():
                with open(HISTORY_FILE, "r") as f:
                    data = json.load(f)
                    self.stage_times = data.get("stage_times", {})
                    # Update estimates based on historical data
                    for stage, times in self.stage_times.items():
                        if times:
                            self.estimates[stage] = sum(times) / len(times)
        except Exception:
            # If we can't load history, just use defaults
            pass

    def _save_history(self):
        """Save deployment times to disk."""
        try:
            HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(HISTORY_FILE, "w") as f:
                json.dump({"stage_times": self.stage_times}, f)
        except Exception:
            # Don't fail if we can't save
            pass

    def record_stage_time(self, stage: str, duration: float):
        """
        Record the duration of a deployment stage.

        Args:
            stage: Stage name (e.g., "build", "upload")
            duration: Time taken in seconds
        """
        if stage not in self.stage_times:
            self.stage_times[stage] = []

        self.stage_times[stage].append(duration)

        # Keep only the last N samples
        if len(self.stage_times[stage]) > self.max_samples:
            self.stage_times[stage] = self.stage_times[stage][-self.max_samples:]

        # Update estimate with rolling average
        self.estimates[stage] = sum(self.stage_times[stage]) / len(self.stage_times[stage])

        # Save to disk periodically
        self._save_history()

    def get_estimate(self, stage: str) -> float:
        """
        Get estimated time for a stage.

        Args:
            stage: Stage name

        Returns:
            Estimated time in seconds
        """
        return self.estimates.get(stage, 10)

    def get_remaining_time(self, current_stage: str, stages: List[str], stage_elapsed: float = 0) -> float:
        """
        Calculate estimated remaining time for deployment.

        Args:
            current_stage: Current deployment stage
            stages: Ordered list of all stages
            stage_elapsed: Time already elapsed in current stage

        Returns:
            Estimated remaining time in seconds
        """
        remaining = 0

        try:
            current_index = stages.index(current_stage)
        except ValueError:
            return 0

        for i, stage in enumerate(stages):
            if i < current_index:
                continue
            elif i == current_index:
                # For current stage, subtract elapsed time
                stage_estimate = self.get_estimate(stage)
                remaining += max(0, stage_estimate - stage_elapsed)
            else:
                remaining += self.get_estimate(stage)

        return remaining


# Global time tracker instance
_time_tracker = DeploymentTimeTracker()


def format_time(seconds: float) -> str:
    """
    Format seconds as human-readable time string.

    Args:
        seconds: Time in seconds

    Returns:
        Formatted string (e.g., "45s", "1m 30s", "2m 5s")
    """
    if seconds < 0:
        return "0s"

    minutes = int(seconds // 60)
    secs = int(seconds % 60)

    if minutes > 0:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


class DeploymentProgress:
    """
    Manages deployment progress tracking with real-time updates.

    Provides a Vercel-style deployment experience:
    - Real-time progress bars
    - Stage-based updates
    - Elapsed time tracking
    - Estimated time remaining (ETA)
    - Clear status messages

    Example:
        with DeploymentProgress(console) as tracker:
            tracker.start_stage("analyze", "Analyzing project...")
            # ... do work ...
            tracker.complete_stage("analyze", "Next.js 16.1.4 detected")

            tracker.start_stage("build", "Building production bundle...")
            # ... do work ...
            tracker.complete_stage("build", "847 KB built")
    """

    def __init__(self, console: Console, show_progress: bool = True, stages: Optional[List[str]] = None):
        """
        Initialize progress tracker.

        Args:
            console: Rich console instance
            show_progress: Whether to show progress bars (False for quiet mode)
            stages: Ordered list of stage names for ETA calculation
        """
        self.console = console
        self.show_progress = show_progress
        self.progress: Optional[Progress] = None
        self.tasks: Dict[str, int] = {}
        self.start_time = time.time()
        self.stages = stages or []
        self.stage_start_times: Dict[str, float] = {}
        self.current_stage: Optional[str] = None
        self.time_tracker = _time_tracker

    def __enter__(self):
        """Start progress tracking."""
        if self.show_progress:
            self.progress = Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TextColumn("[dim]ETA: {task.fields[eta]}[/dim]"),
                TimeElapsedColumn(),
                console=self.console,
            )
            self.progress.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop progress tracking."""
        # Record final stage time
        if self.current_stage and self.current_stage in self.stage_start_times:
            duration = time.time() - self.stage_start_times[self.current_stage]
            self.time_tracker.record_stage_time(self.current_stage, duration)

        if self.progress:
            self.progress.__exit__(exc_type, exc_val, exc_tb)

    def _calculate_eta(self, stage_id: str) -> str:
        """Calculate and format ETA for remaining stages."""
        if not self.stages:
            return "..."

        stage_elapsed = 0
        if stage_id in self.stage_start_times:
            stage_elapsed = time.time() - self.stage_start_times[stage_id]

        remaining = self.time_tracker.get_remaining_time(
            stage_id, self.stages, stage_elapsed
        )

        if remaining <= 0:
            return "< 5s"
        return format_time(remaining)

    def add_stage(self, stage_id: str, description: str, total: int = 100) -> None:
        """
        Add a new deployment stage.

        Args:
            stage_id: Unique identifier for this stage
            description: Human-readable description
            total: Total progress units (default: 100)
        """
        if self.progress:
            eta = self._calculate_eta(stage_id)
            task_id = self.progress.add_task(
                f"[dim]{description}",
                total=total,
                completed=0,
                eta=eta
            )
            self.tasks[stage_id] = task_id

    def start_stage(self, stage_id: str, description: str) -> None:
        """
        Start a deployment stage.

        Args:
            stage_id: Unique identifier for this stage
            description: Human-readable description
        """
        # Record previous stage duration
        if self.current_stage and self.current_stage in self.stage_start_times:
            duration = time.time() - self.stage_start_times[self.current_stage]
            self.time_tracker.record_stage_time(self.current_stage, duration)

        self.current_stage = stage_id
        self.stage_start_times[stage_id] = time.time()

        if stage_id not in self.tasks:
            self.add_stage(stage_id, description)

        if self.progress:
            eta = self._calculate_eta(stage_id)
            self.progress.update(
                self.tasks[stage_id],
                description=f"[cyan]{description}",
                completed=0,
                eta=eta
            )

    def update_stage(
        self,
        stage_id: str,
        completed: int,
        description: Optional[str] = None
    ) -> None:
        """
        Update stage progress.

        Args:
            stage_id: Stage identifier
            completed: Progress percentage (0-100)
            description: Optional new description
        """
        if self.progress and stage_id in self.tasks:
            eta = self._calculate_eta(stage_id)
            kwargs = {"completed": completed, "eta": eta}
            if description:
                kwargs["description"] = f"[cyan]{description}"
            self.progress.update(self.tasks[stage_id], **kwargs)

    def complete_stage(self, stage_id: str, message: Optional[str] = None) -> None:
        """
        Mark stage as complete.

        Args:
            stage_id: Stage identifier
            message: Optional completion message
        """
        # Record stage duration
        if stage_id in self.stage_start_times:
            duration = time.time() - self.stage_start_times[stage_id]
            self.time_tracker.record_stage_time(stage_id, duration)

        if self.progress and stage_id in self.tasks:
            elapsed = time.time() - self.stage_start_times.get(stage_id, time.time())
            time_str = format_time(elapsed)

            if message:
                self.progress.update(
                    self.tasks[stage_id],
                    completed=100,
                    description=f"[green]✓ {message}[/green]",
                    eta=time_str
                )
            else:
                self.progress.update(
                    self.tasks[stage_id],
                    completed=100,
                    eta=time_str
                )

    def fail_stage(self, stage_id: str, error: str) -> None:
        """
        Mark stage as failed.

        Args:
            stage_id: Stage identifier
            error: Error message
        """
        if self.progress and stage_id in self.tasks:
            self.progress.update(
                self.tasks[stage_id],
                description=f"[red]✗ {error}[/red]",
                eta="failed"
            )

    def get_elapsed_time(self) -> int:
        """Get elapsed time since tracking started (in seconds)."""
        return int(time.time() - self.start_time)

    def get_eta(self) -> str:
        """Get formatted estimated time remaining."""
        if self.current_stage:
            return self._calculate_eta(self.current_stage)
        return "..."


class AkashDeploymentProgress(DeploymentProgress):
    """
    Specialized progress tracker for Akash deployments.

    Handles Akash-specific deployment stages:
    1. Analyze project
    2. Build production bundle
    3. Upload to Varity
    4. Deploy to Akash Network
       - Finding providers
       - Creating deployment
       - Waiting for ready status
    """

    def __init__(self, console: Console, show_progress: bool = True):
        super().__init__(console, show_progress)

        # Pre-define Akash deployment stages
        self.stages = {
            "analyze": "Analyzing project...",
            "build": "Building production bundle...",
            "upload": "Uploading to Varity...",
            "deploy": "Deploying to Akash Network...",
        }

    def __enter__(self):
        """Start tracking with pre-defined stages."""
        super().__enter__()

        # Add all stages upfront
        for stage_id, description in self.stages.items():
            self.add_stage(stage_id, description)

        return self

    def handle_akash_update(self, update: dict) -> None:
        """
        Handle progress update from Akash deployer.

        Args:
            update: Progress update from AkashDeployer
                {
                    "stage": "building",
                    "message": "Installing dependencies...",
                    "elapsed": 45
                }
        """
        stage = update.get("stage", "").lower()
        message = update.get("message", "")

        # Map Akash stages to our progress stages
        if stage in ["queued", "pending"]:
            self.complete_stage("upload", "Uploaded to Varity")
            self.update_stage("deploy", 10, message)
        elif stage == "building":
            self.complete_stage("upload", "Uploaded to Varity")
            self.update_stage("deploy", 30, message)
        elif stage in ["deploying", "bidding"]:
            self.update_stage("deploy", 50, message)
        elif stage == "accepting":
            self.update_stage("deploy", 70, message)
        elif stage == "finalizing":
            self.update_stage("deploy", 90, message)
        elif stage == "complete":
            self.complete_stage("deploy", "Deployment complete!")


class IPFSDeploymentProgress(DeploymentProgress):
    """
    Specialized progress tracker for IPFS deployments.

    Handles IPFS-specific deployment stages:
    1. Analyze project
    2. Build production bundle
    3. Upload to IPFS
    """

    def __init__(self, console: Console, show_progress: bool = True):
        super().__init__(console, show_progress)

        # Pre-define IPFS deployment stages
        self.stages = {
            "analyze": "Analyzing project...",
            "build": "Building production bundle...",
            "upload": "Uploading to IPFS...",
        }

    def __enter__(self):
        """Start tracking with pre-defined stages."""
        super().__enter__()

        # Add all stages upfront
        for stage_id, description in self.stages.items():
            self.add_stage(stage_id, description)

        return self
