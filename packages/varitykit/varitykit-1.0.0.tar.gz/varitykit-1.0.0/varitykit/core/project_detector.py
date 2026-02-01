"""
Project detection for various framework types.

This module detects project types by analyzing package.json, configuration files,
and directory structure.

Provides clear, actionable error messages for web2 developers.
"""

import json
from pathlib import Path
from typing import List, Tuple

from .types import ProjectInfo
from .errors import ProjectError


class ProjectDetector:
    """
    Detect project type and configuration.

    Supports:
    - Static HTML (index.html without package.json) - IPFS deployment
    - Next.js (package.json with "next" dependency)
    - React (package.json with "react" but no "next")
    - Vue.js (package.json with "vue")
    - Node.js backend (package.json with "express" or "fastify")
    - Python backend (requirements.txt or pyproject.toml)
    """

    def detect(self, project_path: str) -> ProjectInfo:
        """
        Detect project type by analyzing files in directory.

        Args:
            project_path: Path to the project directory

        Returns:
            ProjectInfo with detected project details

        Raises:
            ProjectDetectionError: If project type cannot be detected
        """
        path = Path(project_path)

        if not path.exists():
            raise ProjectError.path_not_found(project_path)

        # Check for JavaScript/TypeScript project
        package_json_path = path / "package.json"
        if package_json_path.exists():
            return self._detect_js_project(path, package_json_path)

        # Check for Python project
        requirements_path = path / "requirements.txt"
        pyproject_path = path / "pyproject.toml"
        if requirements_path.exists() or pyproject_path.exists():
            return self._detect_python_project(path)

        # Check for static HTML site (index.html without framework)
        index_html_path = path / "index.html"
        if index_html_path.exists():
            return self._detect_static_html(path)

        # Unable to detect - provide helpful message
        raise ProjectError.no_package_json(str(path))

    def _detect_js_project(self, project_path: Path, package_json_path: Path) -> ProjectInfo:
        """
        Detect JavaScript/TypeScript project type.

        Args:
            project_path: Path to the project directory
            package_json_path: Path to package.json

        Returns:
            ProjectInfo for the detected project

        Raises:
            ProjectDetectionError: If project type is unsupported
        """
        try:
            with open(package_json_path, "r", encoding="utf-8") as f:
                package_json = json.load(f)
        except json.JSONDecodeError as e:
            raise ProjectError.invalid_package_json(str(package_json_path), str(e))
        except IOError as e:
            raise ProjectError.invalid_package_json(str(package_json_path), f"Could not read file: {e}")

        # Merge dependencies and devDependencies
        dependencies = {
            **package_json.get("dependencies", {}),
            **package_json.get("devDependencies", {}),
        }

        # Detect package manager
        package_manager = self._detect_package_manager(project_path)

        # Check for backend
        has_backend = (project_path / "server").exists()

        # Detect framework
        if "next" in dependencies:
            return self._detect_nextjs(project_path, dependencies, package_manager, has_backend)

        elif "react" in dependencies or "react-scripts" in dependencies:
            return self._detect_react(project_path, dependencies, package_manager, has_backend)

        elif "vue" in dependencies:
            return self._detect_vue(project_path, dependencies, package_manager, has_backend)

        elif "express" in dependencies or "fastify" in dependencies:
            return self._detect_nodejs(project_path, dependencies, package_manager)

        else:
            # Get list of dependencies for helpful error message
            dep_list = list(dependencies.keys())
            raise ProjectError.unsupported_framework(dep_list)

    def _detect_nextjs(
        self, project_path: Path, dependencies: dict, package_manager: str, has_backend: bool
    ) -> ProjectInfo:
        """Detect Next.js project configuration."""
        # Check if using static export or standalone
        is_static_export = self._is_nextjs_static_export(project_path)
        is_standalone = self._is_nextjs_standalone(project_path)

        # Determine output directory
        if is_static_export:
            output_dir = "out"
        elif is_standalone:
            # For standalone mode, the deployable directory is .next/standalone
            # but we need to detect the app name within the monorepo structure
            resolved_path = project_path.resolve()
            app_name = resolved_path.name
            # Check if it's in a monorepo apps/ directory
            if resolved_path.parent.name == "apps":
                output_dir = f".next/standalone/apps/{app_name}"
            else:
                output_dir = ".next/standalone"
        else:
            output_dir = ".next"

        return ProjectInfo(
            project_type="nextjs",
            framework_version=dependencies.get("next", "unknown"),
            build_command=f"{package_manager} run build",
            output_dir=output_dir,
            package_manager=package_manager,
            has_backend=has_backend or not is_static_export,  # Next.js API routes
        )

    def _detect_react(
        self, project_path: Path, dependencies: dict, package_manager: str, has_backend: bool
    ) -> ProjectInfo:
        """Detect React project configuration (CRA or Vite)."""
        # Check if using Vite
        is_vite = "vite" in dependencies

        return ProjectInfo(
            project_type="react",
            framework_version=dependencies.get("react", "unknown"),
            build_command=f"{package_manager} run build",
            output_dir="dist" if is_vite else "build",
            package_manager=package_manager,
            has_backend=has_backend,
        )

    def _detect_vue(
        self, project_path: Path, dependencies: dict, package_manager: str, has_backend: bool
    ) -> ProjectInfo:
        """Detect Vue.js project configuration."""
        return ProjectInfo(
            project_type="vue",
            framework_version=dependencies.get("vue", "unknown"),
            build_command=f"{package_manager} run build",
            output_dir="dist",
            package_manager=package_manager,
            has_backend=has_backend,
        )

    def _detect_nodejs(
        self, project_path: Path, dependencies: dict, package_manager: str
    ) -> ProjectInfo:
        """Detect Node.js backend project configuration."""
        framework = "express" if "express" in dependencies else "fastify"

        return ProjectInfo(
            project_type="nodejs",
            framework_version=dependencies.get(framework, "unknown"),
            build_command="",  # No build needed for plain Node.js
            output_dir=".",
            package_manager=package_manager,
            has_backend=True,
        )

    def _detect_python_project(self, project_path: Path) -> ProjectInfo:
        """
        Detect Python project configuration.

        Args:
            project_path: Path to the project directory

        Returns:
            ProjectInfo for Python project
        """
        return ProjectInfo(
            project_type="python",
            framework_version=None,
            build_command="",  # Python typically doesn't require build step
            output_dir=".",
            package_manager="pip",
            has_backend=True,
        )

    def _detect_static_html(self, project_path: Path) -> ProjectInfo:
        """
        Detect static HTML website (no build step required).

        This is for simple HTML/CSS/JS sites that can be deployed directly
        to IPFS without any build process. Perfect for landing pages,
        marketing sites, and documentation.

        Args:
            project_path: Path to the project directory

        Returns:
            ProjectInfo for static HTML project
        """
        return ProjectInfo(
            project_type="static",
            framework_version=None,
            build_command="",  # No build required for static HTML
            output_dir=".",  # Deploy the directory as-is
            package_manager=None,
            has_backend=False,
        )

    def _detect_package_manager(self, project_path: Path) -> str:
        """
        Detect package manager (npm, pnpm, yarn).

        Args:
            project_path: Path to the project directory

        Returns:
            Package manager name ('npm', 'pnpm', or 'yarn')
        """
        if (project_path / "pnpm-lock.yaml").exists():
            return "pnpm"
        elif (project_path / "yarn.lock").exists():
            return "yarn"
        else:
            return "npm"

    def _is_nextjs_static_export(self, project_path: Path) -> bool:
        """
        Check if Next.js project uses static export.

        Args:
            project_path: Path to the project directory

        Returns:
            True if using static export (output: 'export')
        """
        # Check next.config.js
        next_config_js = project_path / "next.config.js"
        if next_config_js.exists():
            try:
                content = next_config_js.read_text(encoding="utf-8")
                if 'output: "export"' in content or "output: 'export'" in content:
                    return True
            except IOError:
                pass

        # Check next.config.mjs
        next_config_mjs = project_path / "next.config.mjs"
        if next_config_mjs.exists():
            try:
                content = next_config_mjs.read_text(encoding="utf-8")
                if 'output: "export"' in content or "output: 'export'" in content:
                    return True
            except IOError:
                pass

        # Check next.config.ts
        next_config_ts = project_path / "next.config.ts"
        if next_config_ts.exists():
            try:
                content = next_config_ts.read_text(encoding="utf-8")
                if 'output: "export"' in content or "output: 'export'" in content:
                    return True
            except IOError:
                pass

        return False

    def _is_nextjs_standalone(self, project_path: Path) -> bool:
        """
        Check if Next.js project uses standalone mode.

        Args:
            project_path: Path to the project directory

        Returns:
            True if using standalone mode (output: 'standalone')
        """
        # Check next.config.js
        next_config_js = project_path / "next.config.js"
        if next_config_js.exists():
            try:
                content = next_config_js.read_text(encoding="utf-8")
                if 'output: "standalone"' in content or "output: 'standalone'" in content:
                    return True
            except IOError:
                pass

        # Check next.config.mjs
        next_config_mjs = project_path / "next.config.mjs"
        if next_config_mjs.exists():
            try:
                content = next_config_mjs.read_text(encoding="utf-8")
                if 'output: "standalone"' in content or "output: 'standalone'" in content:
                    return True
            except IOError:
                pass

        # Check next.config.ts
        next_config_ts = project_path / "next.config.ts"
        if next_config_ts.exists():
            try:
                content = next_config_ts.read_text(encoding="utf-8")
                if 'output: "standalone"' in content or "output: 'standalone'" in content:
                    return True
            except IOError:
                pass

        return False

    def detect_hosting_type(self, project_path: str) -> "Tuple[str, str, List[str]]":
        """
        Auto-detect optimal hosting type (IPFS or Akash) based on project features.

        Returns:
            Tuple of (hosting_type, reason, details)
            - hosting_type: 'ipfs' (static) or 'akash' (dynamic)
            - reason: Human-readable summary explanation
            - details: List of specific detected features

        Detection Rules:
        - IPFS (static): Pure HTML/CSS/JS, static site generators, Next.js with output:'export'
        - Akash (dynamic): API routes, SSR, database connections, backend frameworks
        """
        path = Path(project_path)
        details = []

        # Check for pure static HTML (no package.json)
        package_json_path = path / "package.json"
        if not package_json_path.exists():
            index_html = path / "index.html"
            if index_html.exists():
                return (
                    "ipfs",
                    "Pure HTML/CSS/JS site detected",
                    ["No package.json found", "Static HTML files only"]
                )

        # Analyze package.json for framework detection
        try:
            with open(package_json_path, "r", encoding="utf-8") as f:
                package_json = json.load(f)
        except (json.JSONDecodeError, IOError):
            # Default to Akash if we can't read package.json (safer)
            return (
                "akash",
                "Unable to analyze project (defaulting to dynamic hosting)",
                ["Could not read package.json"]
            )

        dependencies = {
            **package_json.get("dependencies", {}),
            **package_json.get("devDependencies", {}),
        }

        framework = self._detect_framework_name(dependencies)
        details.append(f"Framework: {framework}")

        # Check for Next.js
        if "next" in dependencies:
            # Check for static export
            is_static_export = self._is_nextjs_static_export(path)
            if is_static_export:
                details.append("Static export enabled (output: 'export')")
                return (
                    "ipfs",
                    "Next.js static export detected",
                    details
                )

            # Check for API routes
            api_routes = self._detect_nextjs_api_routes(path)
            if api_routes:
                details.append(f"{len(api_routes)} API routes detected")
                details.extend(api_routes[:3])  # Show first 3
                if len(api_routes) > 3:
                    details.append(f"... and {len(api_routes) - 3} more")
                return (
                    "akash",
                    "Next.js with API routes requires server",
                    details
                )

            # Check for server components (app directory)
            if (path / "app").exists():
                details.append("App Router detected (server components)")
                return (
                    "akash",
                    "Next.js App Router requires server-side rendering",
                    details
                )

            # Pages directory without static export = SSR
            if (path / "pages").exists() and not is_static_export:
                details.append("Pages Router without static export")
                return (
                    "akash",
                    "Next.js with SSR requires server",
                    details
                )

        # Check for static site generators
        if any(dep in dependencies for dep in ["vite", "@11ty/eleventy", "gatsby"]):
            static_gen = next((dep for dep in ["vite", "@11ty/eleventy", "gatsby"] if dep in dependencies), None)
            details.append(f"Static site generator: {static_gen}")

            # Vite with SSR plugins requires Akash
            if static_gen == "vite":
                if any(dep in dependencies for dep in ["@vitejs/plugin-react-ssr", "vite-plugin-ssr"]):
                    details.append("SSR plugin detected")
                    return (
                        "akash",
                        "Vite with SSR requires server",
                        details
                    )

            return (
                "ipfs",
                "Static site generator detected",
                details
            )

        # Check for backend frameworks
        backend_frameworks = ["express", "fastify", "koa", "@nestjs/core", "hapi", "restify"]
        detected_backend = [fw for fw in backend_frameworks if fw in dependencies]
        if detected_backend:
            details.append(f"Backend framework: {', '.join(detected_backend)}")
            return (
                "akash",
                "Backend server framework detected",
                details
            )

        # Check for database connections
        database_libs = ["prisma", "@prisma/client", "mongoose", "pg", "mysql2", "typeorm", "sequelize"]
        detected_db = [db for db in database_libs if db in dependencies]
        if detected_db:
            details.append(f"Database: {', '.join(detected_db)}")
            return (
                "akash",
                "Database integration requires server",
                details
            )

        # Check for WebSocket libraries
        websocket_libs = ["socket.io", "ws", "websocket"]
        detected_ws = [ws for ws in websocket_libs if ws in dependencies]
        if detected_ws:
            details.append(f"WebSocket: {', '.join(detected_ws)}")
            return (
                "akash",
                "WebSocket server detected",
                details
            )

        # Check for server-side only frameworks
        ssr_frameworks = ["remix", "@remix-run/node", "nuxt", "@sveltejs/kit"]
        detected_ssr = [fw for fw in ssr_frameworks if fw in dependencies]
        if detected_ssr:
            details.append(f"SSR framework: {', '.join(detected_ssr)}")
            return (
                "akash",
                "Server-side rendering framework detected",
                details
            )

        # Check for React/Vue without server features
        if "react" in dependencies or "vue" in dependencies:
            # Pure client-side React/Vue app
            details.append("Client-side only (no server features detected)")
            return (
                "ipfs",
                "Static client-side application",
                details
            )

        # Default to Akash for unknown configurations (safer)
        details.append("Unknown framework configuration")
        return (
            "akash",
            "Defaulting to dynamic hosting (unknown configuration)",
            details
        )

    def _detect_framework_name(self, dependencies: dict) -> str:
        """Get human-readable framework name from dependencies."""
        if "next" in dependencies:
            version = dependencies["next"]
            return f"Next.js {version}"
        elif "react" in dependencies:
            version = dependencies.get("react", "unknown")
            return f"React {version}"
        elif "vue" in dependencies:
            version = dependencies.get("vue", "unknown")
            return f"Vue {version}"
        elif "vite" in dependencies:
            return "Vite"
        elif "@11ty/eleventy" in dependencies:
            return "Eleventy"
        elif "gatsby" in dependencies:
            return "Gatsby"
        elif "express" in dependencies:
            return "Express"
        elif "fastify" in dependencies:
            return "Fastify"
        else:
            return "Unknown"

    def _detect_nextjs_api_routes(self, project_path: Path) -> List[str]:
        """
        Detect Next.js API routes in both pages and app directories.

        Returns:
            List of detected API route paths
        """
        api_routes = []

        # Check pages/api directory (Pages Router)
        pages_api = project_path / "pages" / "api"
        if pages_api.exists():
            for file in pages_api.rglob("*"):
                if file.is_file() and file.suffix in [".js", ".ts", ".jsx", ".tsx"]:
                    relative_path = file.relative_to(pages_api)
                    api_routes.append(f"/api/{relative_path.with_suffix('')}")

        # Check app/api directory (App Router)
        app_api = project_path / "app" / "api"
        if app_api.exists():
            for file in app_api.rglob("route.*"):
                if file.is_file() and file.suffix in [".js", ".ts"]:
                    relative_path = file.relative_to(app_api).parent
                    api_routes.append(f"/api/{relative_path}")

        return api_routes
