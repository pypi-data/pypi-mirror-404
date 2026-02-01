"""
Template management for VarityKit
"""

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from varitykit.utils.logger import get_logger


@dataclass
class TemplateInfo:
    """Information about a template"""

    name: str
    description: str
    industry: str
    version: str
    repository: Optional[str] = None
    local_path: Optional[Path] = None
    features: Optional[List[str]] = None
    requirements: Optional[Dict[str, str]] = None

    def __post_init__(self):
        if self.features is None:
            self.features = []
        if self.requirements is None:
            self.requirements = {}


class TemplateManager:
    """Manages dashboard templates"""

    OFFICIAL_TEMPLATES = {
        "finance": TemplateInfo(
            name="finance-dashboard",
            description="Financial services dashboard with fraud detection and AML monitoring",
            industry="finance",
            version="1.0.0",
            repository="https://github.com/varity-ai/finance-template.git",
            features=[
                "fraud-detection",
                "aml-monitoring",
                "transaction-analytics",
                "compliance-reporting",
            ],
            requirements={"node": ">=16.0.0", "python": ">=3.10.0"},
        ),
        "healthcare": TemplateInfo(
            name="healthcare-dashboard",
            description="Healthcare management dashboard with HIPAA compliance",
            industry="healthcare",
            version="1.0.0",
            repository="https://github.com/varity-ai/healthcare-template.git",
            features=[
                "patient-management",
                "appointment-scheduling",
                "ehr-integration",
                "hipaa-compliance",
            ],
            requirements={"node": ">=16.0.0", "python": ">=3.10.0"},
        ),
        "retail": TemplateInfo(
            name="retail-dashboard",
            description="Retail management dashboard with inventory and sales analytics",
            industry="retail",
            version="1.0.0",
            repository="https://github.com/varity-ai/retail-template.git",
            features=[
                "inventory-management",
                "sales-analytics",
                "customer-insights",
                "supply-chain",
            ],
            requirements={"node": ">=16.0.0", "python": ">=3.10.0"},
        ),
        "iso-merchant": TemplateInfo(
            name="iso-merchant-dashboard",
            description="ISO merchant services dashboard with payment processing",
            industry="iso-merchant",
            version="1.0.0",
            repository="https://github.com/varity-ai/iso-merchant-template.git",
            features=[
                "merchant-onboarding",
                "payment-processing",
                "residuals-tracking",
                "compliance",
            ],
            requirements={"node": ">=16.0.0", "python": ">=3.10.0"},
        ),
        "generic": TemplateInfo(
            name="generic-dashboard",
            description="Generic business dashboard template",
            industry="generic",
            version="1.0.0",
            repository="https://github.com/varity-ai/generic-template.git",
            features=["data-visualization", "reporting", "user-management"],
            requirements={"node": ">=16.0.0", "python": ">=3.10.0"},
        ),
    }

    def __init__(self, templates_dir: Optional[Path] = None):
        self.logger = get_logger()
        if templates_dir is None:
            # Default to ~/.varity/templates
            self.templates_dir = Path.home() / ".varity" / "templates"
        else:
            self.templates_dir = templates_dir

        self.templates_dir.mkdir(parents=True, exist_ok=True)

    def list_templates(self) -> List[TemplateInfo]:
        """List all available templates"""
        templates: List[TemplateInfo] = []

        # Add official templates
        templates.extend(self.OFFICIAL_TEMPLATES.values())

        # TODO: Add custom/community templates from local directory

        return templates

    def get_template(self, template_name: str) -> Optional[TemplateInfo]:
        """Get template by name"""
        # Check official templates
        if template_name in self.OFFICIAL_TEMPLATES:
            return self.OFFICIAL_TEMPLATES[template_name]

        # Check local templates
        local_template_path = self.templates_dir / template_name
        if local_template_path.exists():
            # Try to load template.json
            template_json = local_template_path / "template.json"
            if template_json.exists():
                try:
                    with open(template_json, "r") as f:
                        data = json.load(f)
                    return TemplateInfo(**data, local_path=local_template_path)
                except Exception as e:
                    self.logger.error(f"Failed to load template {template_name}: {e}")

        return None

    def install_template(self, template_name: str, force: bool = False) -> Path:
        """
        Install template from repository to local templates directory

        Args:
            template_name: Name of the template to install
            force: If True, reinstall even if already exists

        Returns:
            Path to installed template
        """
        template = self.get_template(template_name)
        if template is None:
            raise ValueError(f"Template '{template_name}' not found")

        target_path = self.templates_dir / template_name

        # Check if already installed
        if target_path.exists() and not force:
            self.logger.info(f"Template '{template_name}' already installed at {target_path}")
            return target_path

        # Remove existing if force
        if target_path.exists() and force:
            self.logger.info(f"Removing existing template at {target_path}")
            shutil.rmtree(target_path)

        # Install from repository
        if template.repository:
            self.logger.info(f"Installing template '{template_name}' from {template.repository}")
            try:
                subprocess.run(
                    ["git", "clone", template.repository, str(target_path)],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                self.logger.info(f"Template '{template_name}' installed successfully")
                return target_path
            except subprocess.CalledProcessError as e:
                raise RuntimeError(f"Failed to install template: {e.stderr}")
        else:
            raise ValueError(f"Template '{template_name}' has no repository URL")

    def scaffold_project(
        self,
        template_name: str,
        project_path: Path,
        project_name: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """
        Scaffold a new project from template using Copier

        Args:
            template_name: Name of template to use
            project_path: Path where project should be created
            project_name: Name of the project
            context: Additional context variables for template rendering

        Returns:
            Path to created project
        """
        template = self.get_template(template_name)
        if template is None:
            raise ValueError(f"Template '{template_name}' not found")

        # Ensure template is installed
        if template.repository and not template.local_path:
            template_path = self.install_template(template_name)
        elif template.local_path:
            template_path = template.local_path
        else:
            raise ValueError(f"Template '{template_name}' has no source")

        # Prepare context
        template_context = {
            "project_name": project_name,
            "project_slug": project_name.lower().replace(" ", "-"),
            "industry": template.industry,
            **(context or {}),
        }

        self.logger.info(f"Scaffolding project '{project_name}' from template '{template_name}'")

        try:
            # Use copier to generate project
            # For now, we'll use a simple copy approach
            # TODO: Integrate with copier library for full templating support
            self._copy_template(template_path, project_path, template_context)

            self.logger.info(f"Project scaffolded successfully at {project_path}")
            return project_path

        except Exception as e:
            raise RuntimeError(f"Failed to scaffold project: {e}")

    def _copy_template(self, source: Path, destination: Path, context: Dict[str, Any]):
        """
        Copy template files and render with context
        This is a simplified implementation - will be replaced with Copier integration
        """
        destination.mkdir(parents=True, exist_ok=True)

        # Copy all files except .git
        for item in source.iterdir():
            if item.name == ".git":
                continue

            dest_item = destination / item.name

            if item.is_dir():
                shutil.copytree(item, dest_item, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dest_item)

        # TODO: Render template files with Jinja2
        # For now, just do basic string replacement in package.json and similar files
        self._apply_template_context(destination, context)

    def _apply_template_context(self, project_path: Path, context: Dict[str, Any]):
        """Apply template context to files"""
        # Files to process
        files_to_process = ["package.json", "pyproject.toml", "README.md", ".varitykit.toml"]

        for filename in files_to_process:
            file_path = project_path / filename
            if not file_path.exists():
                continue

            try:
                with open(file_path, "r") as f:
                    content = f.read()

                # Simple string replacement
                for key, value in context.items():
                    placeholder = f"{{{{{key}}}}}"
                    content = content.replace(placeholder, str(value))

                with open(file_path, "w") as f:
                    f.write(content)

            except Exception as e:
                self.logger.warning(f"Failed to process {filename}: {e}")

    def create_custom_template(
        self, template_name: str, source_path: Path, description: str, industry: str
    ) -> TemplateInfo:
        """
        Create a custom template from an existing project

        Args:
            template_name: Name for the template
            source_path: Path to source project
            description: Template description
            industry: Industry category

        Returns:
            Created template info
        """
        target_path = self.templates_dir / template_name

        if target_path.exists():
            raise ValueError(f"Template '{template_name}' already exists")

        # Copy source to templates directory
        shutil.copytree(source_path, target_path)

        # Create template.json
        template_info = TemplateInfo(
            name=template_name,
            description=description,
            industry=industry,
            version="1.0.0",
            local_path=target_path,
        )

        template_json = target_path / "template.json"
        with open(template_json, "w") as f:
            json.dump(
                {
                    "name": template_info.name,
                    "description": template_info.description,
                    "industry": template_info.industry,
                    "version": template_info.version,
                    "features": template_info.features,
                    "requirements": template_info.requirements,
                },
                f,
                indent=2,
            )

        self.logger.info(f"Custom template '{template_name}' created at {target_path}")
        return template_info
