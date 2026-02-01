"""
Build manager for executing project builds.

This module handles building projects based on detected type and framework.
Provides clear, actionable error messages for web2 developers.
"""

import subprocess
import time
from pathlib import Path
from typing import List, Optional

from .types import BuildArtifacts
from .errors import BuildError


class BuildManager:
    """
    Execute build commands and collect artifacts.

    Responsibilities:
    - Run appropriate build command based on project type
    - Stream build output to console
    - Collect build artifacts from output directory
    - Validate build success
    """

    def build(self, project_path: str, build_command: str, output_dir: str) -> BuildArtifacts:
        """
        Execute build command and collect output artifacts.

        Args:
            project_path: Path to the project directory
            build_command: Build command to execute (e.g., 'npm run build')
            output_dir: Expected output directory (e.g., './out', './build')

        Returns:
            BuildArtifacts with file paths, sizes, and timing info

        Raises:
            BuildError: If build fails or output directory is missing
        """
        path = Path(project_path)

        if not path.exists():
            from .errors import ProjectError
            raise ProjectError.path_not_found(project_path)

        # Skip build if no build command (e.g., plain Node.js)
        if not build_command or build_command.strip() == "":
            print("No build command specified, skipping build step")
            return self._collect_artifacts(path, output_dir, 0.0)

        # Check for lockfile (required for reproducible builds)
        package_manager = self._detect_package_manager(path)
        if package_manager:
            self._check_lockfile(path, package_manager)

        # Execute build
        start_time = time.time()
        print(f"\nRunning build command: {build_command}")
        print("-" * 60)

        # Split build command outside try block for error handling
        cmd_parts = build_command.split()
        build_output: List[str] = []

        try:
            # Execute build with real-time output
            process = subprocess.Popen(
                cmd_parts,
                cwd=str(path),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
            )

            # Stream output in real-time and capture it
            if process.stdout:
                for line in process.stdout:
                    print(line, end="")
                    build_output.append(line)

            # Wait for completion
            return_code = process.wait()

            build_time = time.time() - start_time

            if return_code != 0:
                # Capture last 50 lines of output for error details
                output_summary = "".join(build_output[-50:]) if build_output else None
                raise BuildError.failed_with_exit_code(
                    exit_code=return_code,
                    command=build_command,
                    output=output_summary
                )

            print("-" * 60)
            print(f"Build completed successfully in {build_time:.1f}s\n")

        except FileNotFoundError:
            raise BuildError.command_not_found(
                command=build_command,
                package_manager=package_manager or "npm"
            )
        except subprocess.SubprocessError as e:
            raise BuildError.failed_with_exit_code(
                exit_code=-1,
                command=build_command,
                output=str(e)
            )

        # Collect build artifacts
        return self._collect_artifacts(path, output_dir, build_time)

    def _collect_artifacts(
        self, project_path: Path, output_dir: str, build_time: float
    ) -> BuildArtifacts:
        """
        Collect build artifacts from output directory.

        Args:
            project_path: Path to the project directory
            output_dir: Output directory relative to project_path
            build_time: Time taken to build in seconds

        Returns:
            BuildArtifacts with collected files

        Raises:
            BuildError: If output directory is missing or empty
        """
        build_path = project_path / output_dir

        # Check if build directory exists
        if not build_path.exists():
            # Try common alternative directories
            alternatives = self._get_alternative_dirs(project_path)
            found_alternative = None

            for alt_dir in alternatives:
                if (project_path / alt_dir).exists():
                    found_alternative = alt_dir
                    build_path = project_path / alt_dir
                    print(f"Note: Using {alt_dir} instead of {output_dir}")
                    break

            if not found_alternative:
                raise BuildError.output_not_found(
                    expected_dir=str(build_path),
                    alternatives=alternatives
                )

        # Collect all files recursively
        all_files = list(build_path.rglob("*"))
        files = [f for f in all_files if f.is_file()]

        if not files:
            raise BuildError.empty_output(output_dir=str(build_path))

        # Calculate total size
        total_size_bytes = sum(f.stat().st_size for f in files)
        total_size_mb = total_size_bytes / (1024 * 1024)

        # Get relative paths
        relative_files = [str(f.relative_to(build_path)) for f in files]

        # Determine entrypoint
        entrypoint = self._determine_entrypoint(build_path)

        print(f"Collected {len(files)} files ({total_size_mb:.2f} MB)")

        return BuildArtifacts(
            success=True,
            output_dir=str(build_path),
            files=relative_files,
            entrypoint=entrypoint,
            total_size_mb=total_size_mb,
            build_time_seconds=build_time,
        )

    def _get_alternative_dirs(self, project_path: Path) -> List[str]:
        """
        Get alternative build directories to check.

        Args:
            project_path: Path to the project directory

        Returns:
            List of alternative directory names
        """
        return ["build", "dist", "out", ".next", "public"]

    def _determine_entrypoint(self, build_path: Path) -> str:
        """
        Determine the entrypoint file for the build.

        Args:
            build_path: Path to the build directory

        Returns:
            Entrypoint filename (e.g., 'index.html')
        """
        # Check for common entrypoint files
        common_entrypoints = ["index.html", "index.htm", "main.html", "app.html"]

        for entrypoint in common_entrypoints:
            if (build_path / entrypoint).exists():
                return entrypoint

        # For Next.js .next directory
        if build_path.name == ".next":
            return "server.js"  # Next.js server entrypoint

        # Default to index.html
        return "index.html"

    def _detect_package_manager(self, project_path: Path) -> Optional[str]:
        """
        Detect which package manager the project uses.

        Args:
            project_path: Path to the project directory

        Returns:
            Package manager name ('npm', 'pnpm', 'yarn') or None
        """
        if (project_path / "pnpm-lock.yaml").exists():
            return "pnpm"
        elif (project_path / "yarn.lock").exists():
            return "yarn"
        elif (project_path / "package-lock.json").exists():
            return "npm"
        elif (project_path / "package.json").exists():
            # Has package.json but no lockfile - assume npm
            return "npm"
        return None

    def _check_lockfile(self, project_path: Path, package_manager: str) -> None:
        """
        Check that the appropriate lockfile exists for the package manager.

        Args:
            project_path: Path to the project directory
            package_manager: Detected package manager

        Raises:
            BuildError: If lockfile is missing
        """
        lockfile_map = {
            "npm": "package-lock.json",
            "yarn": "yarn.lock",
            "pnpm": "pnpm-lock.yaml",
        }

        lockfile = lockfile_map.get(package_manager)
        if lockfile and not (project_path / lockfile).exists():
            # Only warn, don't fail - some projects work without lockfiles
            print(f"\n[Warning] No {lockfile} found. For reproducible builds,")
            print(f"         run '{package_manager} install' and commit the lockfile.\n")
