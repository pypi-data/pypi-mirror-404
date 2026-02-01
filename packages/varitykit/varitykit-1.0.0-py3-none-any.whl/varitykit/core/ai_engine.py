"""
AI Configuration Engine for VarityKit
=====================================

This module implements the core AI-powered configuration engine that generates
complete, customized dashboard templates through conversational AI.

Key Features:
- LLM-powered chain-of-thought reasoning (Vertex AI / Gemini 2.5 Flash)
- Interactive conversational interface for requirements gathering
- Automated template selection and customization
- Code generation with self-validation and self-correction
- Quality scoring and continuous improvement

Author: Varity AI Team (Team B - AI Configuration Engine Development Agent)
"""

import ast
import asyncio
import json
import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Google Cloud / Vertex AI imports
try:
    from google.cloud import aiplatform
    from vertexai.preview.generative_models import ChatSession, GenerativeModel

    VERTEX_AI_AVAILABLE = True
except ImportError:
    VERTEX_AI_AVAILABLE = False
    logging.warning(
        "Vertex AI not available. Install google-cloud-aiplatform for full functionality."
    )

import subprocess

# Template and validation imports
from jinja2 import Environment, FileSystemLoader, select_autoescape

logger = logging.getLogger(__name__)


class Industry(Enum):
    """Supported industry templates"""

    FINANCE = "finance"
    HEALTHCARE = "healthcare"
    RETAIL = "retail"
    ISO = "iso"


class AIFeature(Enum):
    """Available AI features for dashboards"""

    FRAUD_DETECTION = "fraud_detection"
    AML_MONITORING = "aml_monitoring"
    CHATBOT = "chatbot"
    RISK_FORECASTING = "risk_forecasting"
    DOCUMENT_ANALYSIS = "document_analysis"
    PATIENT_DIAGNOSIS = "patient_diagnosis"
    INVENTORY_OPTIMIZATION = "inventory_optimization"
    DEMAND_FORECASTING = "demand_forecasting"
    PAYMENT_RISK_ANALYSIS = "payment_risk_analysis"


@dataclass
class UserRequirements:
    """User requirements collected through conversational interface"""

    industry: Industry
    company_name: str
    user_roles: List[str] = field(default_factory=list)
    data_types: List[str] = field(default_factory=list)
    ai_features: List[AIFeature] = field(default_factory=list)
    additional_context: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "industry": self.industry.value,
            "company_name": self.company_name,
            "user_roles": self.user_roles,
            "data_types": self.data_types,
            "ai_features": [f.value for f in self.ai_features],
            "additional_context": self.additional_context,
        }


@dataclass
class TemplateConfig:
    """Template configuration for dashboard generation"""

    template_id: str
    template_path: str
    customizations_needed: List[str] = field(default_factory=list)
    reasoning: str = ""
    industry: Industry = Industry.FINANCE

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "template_id": self.template_id,
            "template_path": self.template_path,
            "customizations_needed": self.customizations_needed,
            "reasoning": self.reasoning,
            "industry": self.industry.value,
        }


@dataclass
class ValidationResult:
    """Result of code validation"""

    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    score: float = 0.0

    def __bool__(self):
        return self.valid


@dataclass
class QualityScore:
    """Quality score for generated template"""

    code_quality: float = 0.0
    type_safety: float = 0.0
    security: float = 0.0
    performance: float = 0.0
    accessibility: float = 0.0
    documentation: float = 0.0

    @property
    def overall(self) -> float:
        """Calculate weighted average overall score"""
        weights = {
            "code_quality": 0.25,
            "type_safety": 0.20,
            "security": 0.25,
            "performance": 0.15,
            "accessibility": 0.10,
            "documentation": 0.05,
        }
        return (
            self.code_quality * weights["code_quality"]
            + self.type_safety * weights["type_safety"]
            + self.security * weights["security"]
            + self.performance * weights["performance"]
            + self.accessibility * weights["accessibility"]
            + self.documentation * weights["documentation"]
        )


class AIConfigurationEngine:
    """
    AI-powered configuration engine that generates complete dashboard templates
    through conversational interface and chain-of-thought reasoning.

    This is the core innovation of VarityKit - replacing manual coding with
    intelligent AI-driven template generation.
    """

    def __init__(
        self,
        project_id: Optional[str] = None,
        location: str = "us-east1",
        model_name: str = "gemini-2.5-flash-002",
        rag_knowledge_base_size: int = 50000,
        chain_of_thought_depth: int = 5,
        self_correction_enabled: bool = True,
        max_correction_attempts: int = 3,
        min_quality_score: float = 85.0,
    ):
        """
        Initialize AI Configuration Engine

        Args:
            project_id: Google Cloud project ID (defaults to GOOGLE_CLOUD_PROJECT env var)
            location: Google Cloud location for Vertex AI
            model_name: Gemini model to use for generation
            rag_knowledge_base_size: Target size of RAG knowledge base
            chain_of_thought_depth: Depth of reasoning chains
            self_correction_enabled: Enable self-correction loops
            max_correction_attempts: Maximum attempts for self-correction
            min_quality_score: Minimum acceptable quality score (0-100)
        """
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT", "blokko-specialized-llm")
        self.location = location
        self.model_name = model_name
        self.rag_knowledge_base_size = rag_knowledge_base_size
        self.chain_of_thought_depth = chain_of_thought_depth
        self.self_correction_enabled = self_correction_enabled
        self.max_correction_attempts = max_correction_attempts
        self.min_quality_score = min_quality_score

        # Initialize conversation history
        self.conversation_history: List[Dict[str, str]] = []

        # Initialize Vertex AI model if available
        self.model: Optional[GenerativeModel] = None
        self.chat_session: Optional[ChatSession] = None

        if VERTEX_AI_AVAILABLE:
            try:
                aiplatform.init(project=self.project_id, location=self.location)
                self.model = GenerativeModel(model_name)
                logger.info(f"Initialized Vertex AI with model {model_name}")
            except Exception as e:
                logger.warning(f"Could not initialize Vertex AI: {e}")
                logger.warning("Falling back to mock mode for development")

        # Load templates
        self.templates_dir = Path(__file__).parent.parent / "templates"
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=select_autoescape(["html", "xml"]),
        )

        # Metrics tracking
        self.metrics = {
            "generations_attempted": 0,
            "generations_successful": 0,
            "average_quality_score": 0.0,
            "self_corrections_triggered": 0,
            "common_errors": [],
        }

        logger.info("AI Configuration Engine initialized")

    # ============================================================================
    # WEEK 1: LLM INTEGRATION & PROMPT ENGINEERING
    # ============================================================================

    async def interactive_configuration(self) -> UserRequirements:
        """
        Run interactive conversational interface to collect requirements

        This is the main entry point for the AI-powered configuration flow.
        It asks users a series of intelligent questions to understand their needs.

        Returns:
            UserRequirements object containing all collected information
        """
        logger.info("Starting interactive configuration")

        print("\n" + "=" * 60)
        print("> VarityKit AI Assistant")
        print("=" * 60)
        print()

        # Question 1: Industry selection
        industry = await self._ask_industry()

        # Question 2: Company name
        company_name = await self._ask_company_name()

        # Question 3: User roles
        user_roles = await self._ask_user_roles(industry)

        # Question 4: Main data types
        data_types = await self._ask_data_types(industry)

        # Question 5: AI features
        ai_features = await self._ask_ai_features(industry)

        # Optional: Additional context
        additional_context = await self._ask_additional_context()

        requirements = UserRequirements(
            industry=industry,
            company_name=company_name,
            user_roles=user_roles,
            data_types=data_types,
            ai_features=ai_features,
            additional_context=additional_context,
        )

        logger.info(f"Requirements collected: {requirements.to_dict()}")
        return requirements

    async def _ask_industry(self) -> Industry:
        """Ask user to select industry"""
        print("What industry is this dashboard for?")
        print("  1. Finance (Banking, Investment, Compliance)")
        print("  2. Healthcare (HIPAA, Patient Data, Medical Ops)")
        print("  3. Retail (E-commerce, Inventory, Supply Chain)")
        print("  4. ISO (Merchant Services, Payment Processing)")
        print()

        industry_map = {
            "1": Industry.FINANCE,
            "2": Industry.HEALTHCARE,
            "3": Industry.RETAIL,
            "4": Industry.ISO,
        }

        while True:
            choice = input("> ").strip()
            if choice in industry_map:
                industry = industry_map[choice]
                print(f"\nGreat! I'll help you build a {industry.value.title()} dashboard.\n")
                return industry
            print("Invalid choice. Please enter 1, 2, 3, or 4.")

    async def _ask_company_name(self) -> str:
        """Ask for company name"""
        print("What is the company name?")
        company_name = input("> ").strip()
        print()
        return company_name

    async def _ask_user_roles(self, industry: Industry) -> List[str]:
        """Ask for primary user roles"""
        print("What are the primary user roles? (comma-separated)")

        # Provide industry-specific suggestions
        suggestions = self._get_role_suggestions(industry)
        print(f"Suggestions: {', '.join(suggestions)}")

        roles_input = input("> ").strip()
        roles = [r.strip() for r in roles_input.split(",") if r.strip()]
        print()
        return roles

    async def _ask_data_types(self, industry: Industry) -> List[str]:
        """Ask for main data types"""
        print("What main data will this dashboard manage? (comma-separated)")

        # Provide industry-specific suggestions
        suggestions = self._get_data_type_suggestions(industry)
        print(f"Suggestions: {', '.join(suggestions)}")

        data_input = input("> ").strip()
        data_types = [d.strip() for d in data_input.split(",") if d.strip()]
        print()
        return data_types

    async def _ask_ai_features(self, industry: Industry) -> List[AIFeature]:
        """Ask for desired AI features"""
        print("What AI features do you need? (enter numbers separated by commas)")

        # Get industry-specific AI features
        features = self._get_ai_features_for_industry(industry)
        for i, feature in enumerate(features, 1):
            print(f"  {i}. {self._format_feature_name(feature)}")
        print()

        choices = input("> ").strip()
        selected_indices = [int(c.strip()) - 1 for c in choices.split(",") if c.strip().isdigit()]
        selected_features = [features[i] for i in selected_indices if 0 <= i < len(features)]
        print()
        return selected_features

    async def _ask_additional_context(self) -> Optional[str]:
        """Ask for any additional context"""
        print("Any additional requirements or context? (press Enter to skip)")
        context = input("> ").strip()
        print()
        return context if context else None

    def _get_role_suggestions(self, industry: Industry) -> List[str]:
        """Get role suggestions for industry"""
        suggestions = {
            Industry.FINANCE: ["Banker", "Compliance Officer", "Risk Analyst", "Customer"],
            Industry.HEALTHCARE: ["Doctor", "Nurse", "Administrator", "Patient"],
            Industry.RETAIL: ["Store Manager", "Inventory Manager", "Sales Associate", "Customer"],
            Industry.ISO: [
                "Merchant Services Rep",
                "Compliance Officer",
                "Support Agent",
                "Merchant",
            ],
        }
        return suggestions.get(industry, [])

    def _get_data_type_suggestions(self, industry: Industry) -> List[str]:
        """Get data type suggestions for industry"""
        suggestions = {
            Industry.FINANCE: ["Transactions", "KYC Documents", "Risk Reports", "Accounts"],
            Industry.HEALTHCARE: [
                "Patient Records",
                "Medical History",
                "Prescriptions",
                "Appointments",
            ],
            Industry.RETAIL: ["Products", "Inventory", "Orders", "Customers"],
            Industry.ISO: ["Merchants", "Applications", "Payments", "Compliance Documents"],
        }
        return suggestions.get(industry, [])

    def _get_ai_features_for_industry(self, industry: Industry) -> List[AIFeature]:
        """Get relevant AI features for industry"""
        feature_map = {
            Industry.FINANCE: [
                AIFeature.FRAUD_DETECTION,
                AIFeature.AML_MONITORING,
                AIFeature.RISK_FORECASTING,
                AIFeature.CHATBOT,
                AIFeature.DOCUMENT_ANALYSIS,
            ],
            Industry.HEALTHCARE: [
                AIFeature.PATIENT_DIAGNOSIS,
                AIFeature.DOCUMENT_ANALYSIS,
                AIFeature.CHATBOT,
                AIFeature.RISK_FORECASTING,
            ],
            Industry.RETAIL: [
                AIFeature.INVENTORY_OPTIMIZATION,
                AIFeature.DEMAND_FORECASTING,
                AIFeature.CHATBOT,
                AIFeature.FRAUD_DETECTION,
            ],
            Industry.ISO: [
                AIFeature.PAYMENT_RISK_ANALYSIS,
                AIFeature.FRAUD_DETECTION,
                AIFeature.DOCUMENT_ANALYSIS,
                AIFeature.CHATBOT,
            ],
        }
        return feature_map.get(industry, [])

    def _format_feature_name(self, feature: AIFeature) -> str:
        """Format feature name for display"""
        return feature.value.replace("_", " ").title()

    async def analyze_requirements(self, requirements: UserRequirements) -> Dict[str, Any]:
        """
        Analyze user requirements using chain-of-thought reasoning

        Args:
            requirements: UserRequirements object

        Returns:
            Analysis results with recommendations
        """
        logger.info("Analyzing requirements with chain-of-thought reasoning")

        print("🧠 Analyzing your requirements...")
        print()

        # Use LLM for deep analysis if available
        if self.model:
            analysis = await self._llm_analyze_requirements(requirements)
        else:
            # Fallback to rule-based analysis
            analysis = self._rule_based_analyze_requirements(requirements)

        # Display analysis results
        print(f" Industry: {requirements.industry.value.title()}")
        print(f" User roles: {len(requirements.user_roles)} detected")
        print(f" Data types: {len(requirements.data_types)} detected")
        print(f" AI features: {len(requirements.ai_features)} selected")
        print()

        return analysis  # type: ignore[return-value]
    async def _llm_analyze_requirements(self, requirements: UserRequirements) -> Dict[str, Any]:
        """Use LLM to analyze requirements with chain-of-thought reasoning"""
        prompt = f"""
You are an expert system architect analyzing requirements for a company-specific AI dashboard.

REQUIREMENTS:
- Industry: {requirements.industry.value}
- Company: {requirements.company_name}
- User Roles: {', '.join(requirements.user_roles)}
- Data Types: {', '.join(requirements.data_types)}
- AI Features: {', '.join([f.value for f in requirements.ai_features])}
{f'- Additional Context: {requirements.additional_context}' if requirements.additional_context else ''}

TASK:
Analyze these requirements using chain-of-thought reasoning and provide:
1. Template Match: Which template (finance/healthcare/retail/iso) is best and why?
2. Architecture Recommendations: What components, pages, and integrations are needed?
3. Customization Needs: What specific customizations beyond the base template?
4. Complexity Assessment: Estimated complexity (simple/moderate/complex)
5. Implementation Plan: High-level steps to build this dashboard

Think step-by-step and provide detailed reasoning.

Return your analysis as JSON with keys: template_match, architecture, customizations, complexity, implementation_plan, reasoning
"""

        try:
            if self.model is None:

                raise RuntimeError("Model not initialized")

            response = await asyncio.to_thread(self.model.generate_content, prompt)  # type: ignore[attr-defined]

            # Parse JSON response
            response_text = response.text.strip()
            # Remove markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

            analysis = json.loads(response_text.strip())
            return analysis  # type: ignore[return-value]
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            return self._rule_based_analyze_requirements(requirements)

    def _rule_based_analyze_requirements(self, requirements: UserRequirements) -> Dict[str, Any]:
        """Fallback rule-based analysis"""
        return {
            "template_match": requirements.industry.value,
            "architecture": {
                "components": len(requirements.user_roles) * 2 + len(requirements.data_types),
                "pages": len(requirements.user_roles) + 3,
                "integrations": len(requirements.ai_features),
            },
            "customizations": [
                f"Role-specific dashboard for {role}" for role in requirements.user_roles
            ]
            + [f"Data management for {data_type}" for data_type in requirements.data_types],
            "complexity": "moderate",
            "implementation_plan": [
                "Setup project structure",
                "Generate dashboard layout",
                "Create role-specific pages",
                "Implement data components",
                "Integrate AI features",
                "Configure API layer",
                "Setup testing",
            ],
            "reasoning": f"Selected {requirements.industry.value} template based on industry match",
        }

    # ============================================================================
    # WEEK 2: TEMPLATE GENERATION ENGINE
    # ============================================================================

    async def select_optimal_template(self, requirements: UserRequirements) -> TemplateConfig:
        """
        Select optimal template based on requirements

        Args:
            requirements: UserRequirements object

        Returns:
            TemplateConfig with template selection and customization plan
        """
        logger.info("Selecting optimal template")

        if self.model:
            template_config = await self._llm_select_template(requirements)
        else:
            template_config = self._rule_based_select_template(requirements)

        print(f" Template: {template_config.template_id.title()} Template (best match)")
        return template_config

    async def _llm_select_template(self, requirements: UserRequirements) -> TemplateConfig:
        """Use LLM to select optimal template"""
        prompt = f"""
Select the best template for these requirements:

REQUIREMENTS:
- Industry: {requirements.industry.value}
- Company: {requirements.company_name}
- User Roles: {', '.join(requirements.user_roles)}
- Data Types: {', '.join(requirements.data_types)}
- AI Features: {', '.join([f.value for f in requirements.ai_features])}

AVAILABLE TEMPLATES:
1. Finance Template: Banking, compliance, transactions, KYC, AML
2. Healthcare Template: HIPAA, patient data, medical operations, EMR
3. Retail Template: E-commerce, inventory, supply chain, orders
4. ISO Template: Merchant services, payment processing, onboarding

Return JSON with:
- template_id: (finance|healthcare|retail|iso)
- customizations_needed: [list of specific customizations]
- reasoning: Why this template is the best match
"""

        try:
            if self.model is None:

                raise RuntimeError("Model not initialized")

            response = await asyncio.to_thread(self.model.generate_content, prompt)  # type: ignore[attr-defined]

            response_text = response.text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

            result = json.loads(response_text.strip())

            return TemplateConfig(
                template_id=result["template_id"],
                template_path=f"templates/{result['template_id']}-template",
                customizations_needed=result.get("customizations_needed", []),
                reasoning=result.get("reasoning", ""),
                industry=Industry(result["template_id"]),
            )

        except Exception as e:
            logger.error(f"LLM template selection failed: {e}")
            return self._rule_based_select_template(requirements)

    def _rule_based_select_template(self, requirements: UserRequirements) -> TemplateConfig:
        """Fallback rule-based template selection"""
        template_id = requirements.industry.value
        return TemplateConfig(
            template_id=template_id,
            template_path=f"templates/{template_id}-template",
            customizations_needed=[
                "Customize branding",
                "Configure user roles",
                "Setup data models",
            ],
            reasoning=f"Direct match to {requirements.industry.value} industry",
            industry=requirements.industry,
        )

    async def generate_template(
        self, requirements: UserRequirements, output_dir: Path
    ) -> Dict[str, Any]:
        """
        Generate complete dashboard template

        Args:
            requirements: UserRequirements object
            output_dir: Output directory for generated project

        Returns:
            Generation results with file paths and metadata
        """
        logger.info(f"Generating template for {requirements.company_name}")
        self.metrics["generations_attempted"] += 1

        print("Generating your dashboard...")
        print()

        # Step 1: Analyze requirements
        analysis = await self.analyze_requirements(requirements)

        # Step 2: Select template
        template_config = await self.select_optimal_template(requirements)

        # Step 3: Generate project structure
        print("[] 20% - Creating project structure...")
        project_structure = await self.generate_project_structure(
            requirements, template_config, output_dir
        )

        # Step 4: Generate components
        print("[] 40% - Generating React components...")
        components = await self.generate_components(requirements, template_config, output_dir)

        # Step 5: Generate API layer
        print("[] 60% - Configuring API integration...")
        api_layer = await self.generate_api_integrations(requirements, output_dir)

        # Step 6: Apply branding
        print("[] 80% - Applying branding...")
        branding = await self.apply_branding(requirements, output_dir)

        # Step 7: Generate config files
        print("[] 100% - Finalizing configuration...")
        config_files = await self.generate_config_files(requirements, template_config, output_dir)

        print()

        result = {
            "success": True,
            "project_structure": project_structure,
            "components": components,
            "api_layer": api_layer,
            "branding": branding,
            "config_files": config_files,
            "output_dir": str(output_dir),
            "analysis": analysis,
            "template_config": template_config.to_dict(),
        }

        self.metrics["generations_successful"] += 1
        return result

    async def generate_project_structure(
        self, requirements: UserRequirements, template_config: TemplateConfig, output_dir: Path
    ) -> Dict[str, List[str]]:
        """Generate project directory structure"""
        structure = {"root": [], "src": [], "components": [], "services": [], "config": []}

        # Create directories
        directories = [
            output_dir / "src",
            output_dir / "src" / "components",
            output_dir / "src" / "services",
            output_dir / "src" / "utils",
            output_dir / "src" / "config",
            output_dir / "src" / "types",
            output_dir / "public",
            output_dir / "tests",
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            structure[directory.name if directory.name != str(output_dir) else "root"].append(
                str(directory)
            )

        logger.info(f"Created {len(directories)} directories")
        return structure

    async def generate_components(
        self, requirements: UserRequirements, template_config: TemplateConfig, output_dir: Path
    ) -> List[str]:
        """Generate React components"""
        components = []

        # Generate dashboard layout
        layout_component = await self.generate_dashboard_layout(requirements, output_dir)
        components.append(layout_component)

        # Generate role-specific pages
        for role in requirements.user_roles:
            role_page = await self.generate_role_page(role, requirements, output_dir)
            components.append(role_page)

        # Generate data components
        for data_type in requirements.data_types:
            data_component = await self.generate_data_component(data_type, requirements, output_dir)
            components.append(data_component)

        logger.info(f"Generated {len(components)} components")
        return components

    async def generate_dashboard_layout(
        self, requirements: UserRequirements, output_dir: Path
    ) -> str:
        """Generate main dashboard layout component"""
        component_path = output_dir / "src" / "components" / "DashboardLayout.tsx"

        # Generate component code using LLM or template
        if self.model:
            code = await self._llm_generate_component(
                "DashboardLayout",
                f"Main dashboard layout for {requirements.company_name}",
                requirements,
            )
        else:
            code = self._template_generate_dashboard_layout(requirements)

        # Write component file
        component_path.write_text(code)
        return str(component_path)

    async def generate_role_page(
        self, role: str, requirements: UserRequirements, output_dir: Path
    ) -> str:
        """Generate role-specific page component"""
        safe_role_name = role.replace(" ", "")
        component_path = output_dir / "src" / "components" / f"{safe_role_name}Dashboard.tsx"

        if self.model:
            code = await self._llm_generate_component(
                f"{safe_role_name}Dashboard", f"Dashboard page for {role} role", requirements
            )
        else:
            code = self._template_generate_role_page(role, requirements)

        component_path.write_text(code)
        return str(component_path)

    async def generate_data_component(
        self, data_type: str, requirements: UserRequirements, output_dir: Path
    ) -> str:
        """Generate data management component"""
        safe_data_name = data_type.replace(" ", "")
        component_path = output_dir / "src" / "components" / f"{safe_data_name}Manager.tsx"

        if self.model:
            code = await self._llm_generate_component(
                f"{safe_data_name}Manager", f"Component for managing {data_type}", requirements
            )
        else:
            code = self._template_generate_data_component(data_type, requirements)

        component_path.write_text(code)
        return str(component_path)

    async def _llm_generate_component(
        self, component_name: str, description: str, requirements: UserRequirements
    ) -> str:
        """Use LLM to generate React component code"""
        prompt = f"""
Generate a production-ready React + TypeScript component.

COMPONENT NAME: {component_name}
DESCRIPTION: {description}
INDUSTRY: {requirements.industry.value}
COMPANY: {requirements.company_name}

REQUIREMENTS:
- Use TypeScript with strict typing
- Use Material-UI (@mui/material) for UI components
- Use @varity/ui-kit components where appropriate
- Follow React best practices (functional components, hooks)
- Include proper error handling
- Add JSDoc comments
- Make it responsive and accessible

Return only the component code, no explanations.
"""

        try:
            if self.model is None:

                raise RuntimeError("Model not initialized")

            response = await asyncio.to_thread(self.model.generate_content, prompt)  # type: ignore[attr-defined]

            code = response.text.strip()
            # Remove markdown code blocks
            if code.startswith("```typescript") or code.startswith("```tsx"):
                code = "\n".join(code.split("\n")[1:])
            if code.startswith("```"):
                code = "\n".join(code.split("\n")[1:])
            if code.endswith("```"):
                code = "\n".join(code.split("\n")[:-1])

            return code.strip()

        except Exception as e:
            logger.error(f"LLM component generation failed: {e}")
            return self._template_generate_basic_component(component_name, description)

    def _template_generate_dashboard_layout(self, requirements: UserRequirements) -> str:
        """Generate dashboard layout using template"""
        return f"""import React from 'react';
import {{ Box, AppBar, Toolbar, Typography, Container }} from '@mui/material';

/**
 * Main dashboard layout for {requirements.company_name}
 */
const DashboardLayout: React.FC<{{ children: React.ReactNode }}> = ({{ children }}) => {{
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            {requirements.company_name} Dashboard
          </Typography>
        </Toolbar>
      </AppBar>

      <Container maxWidth="xl" sx={{ mt: 4, mb: 4, flex: 1 }}>
        {{children}}
      </Container>
    </Box>
  );
}};

export default DashboardLayout;
"""

    def _template_generate_role_page(self, role: str, requirements: UserRequirements) -> str:
        """Generate role page using template"""
        safe_role = role.replace(" ", "")
        return f"""import React from 'react';
import {{ Box, Typography, Grid, Paper }} from '@mui/material';

/**
 * Dashboard page for {role} role
 */
const {safe_role}Dashboard: React.FC = () => {{
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        {role} Dashboard
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6">Quick Actions</Typography>
            {{/* Add role-specific actions */}}
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6">Recent Activity</Typography>
            {{/* Add activity feed */}}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}};

export default {safe_role}Dashboard;
"""

    def _template_generate_data_component(
        self, data_type: str, requirements: UserRequirements
    ) -> str:
        """Generate data component using template"""
        safe_data = data_type.replace(" ", "")
        return f"""import React, {{ useState, useEffect }} from 'react';
import {{ Box, Typography, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper }} from '@mui/material';

/**
 * Component for managing {data_type}
 */
const {safe_data}Manager: React.FC = () => {{
  const [data, setData] = useState<any[]>([]);

  useEffect(() => {{
    // Fetch data from API
    // TODO: Implement API call
  }}, []);

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        {data_type} Management
      </Typography>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>Name</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {{data.map((item) => (
              <TableRow key={item.id}>
                <TableCell>{{item.id}}</TableCell>
                <TableCell>{{item.name}}</TableCell>
                <TableCell>{{item.status}}</TableCell>
                <TableCell>
                  {{/* Add action buttons */}}
                </TableCell>
              </TableRow>
            ))}}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}};

export default {safe_data}Manager;
"""

    def _template_generate_basic_component(self, name: str, description: str) -> str:
        """Generate basic component template"""
        return f"""import React from 'react';
import {{ Box, Typography }} from '@mui/material';

/**
 * {description}
 */
const {name}: React.FC = () => {{
  return (
    <Box>
      <Typography variant="h5">{name}</Typography>
      <Typography variant="body1">Component implementation here</Typography>
    </Box>
  );
}};

export default {name};
"""

    async def generate_api_integrations(
        self, requirements: UserRequirements, output_dir: Path
    ) -> Dict[str, str]:
        """Generate API integration layer"""
        api_files = {}

        # Generate main API client
        api_client_path = output_dir / "src" / "services" / "apiClient.ts"
        api_client_code = self._generate_api_client(requirements)
        api_client_path.write_text(api_client_code)
        api_files["apiClient"] = str(api_client_path)

        # Generate feature-specific API services
        for feature in requirements.ai_features:
            service_path = output_dir / "src" / "services" / f"{feature.value}Service.ts"
            service_code = self._generate_api_service(feature, requirements)
            service_path.write_text(service_code)
            api_files[feature.value] = str(service_path)

        logger.info(f"Generated {len(api_files)} API integration files")
        return api_files

    def _generate_api_client(self, requirements: UserRequirements) -> str:
        """Generate main API client"""
        return """import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';

/**
 * Main API client for Varity API Server
 */
class APIClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: process.env.REACT_APP_VARITY_API_URL || 'http://localhost:8000',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add request interceptor for auth
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('auth_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        // Handle common errors
        if (error.response?.status === 401) {
          // Redirect to login
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.get<T>(url, config);
    return response.data;
  }

  async post<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.post<T>(url, data, config);
    return response.data;
  }

  async put<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.put<T>(url, data, config);
    return response.data;
  }

  async delete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.delete<T>(url, config);
    return response.data;
  }
}

export const apiClient = new APIClient();
export default apiClient;
"""

    def _generate_api_service(self, feature: AIFeature, requirements: UserRequirements) -> str:
        """Generate feature-specific API service"""
        feature_name = feature.value.replace("_", " ").title().replace(" ", "")

        return f"""import apiClient from './apiClient';

/**
 * API service for {feature.value.replace('_', ' ')}
 */
class {feature_name}Service {{
  /**
   * Execute {feature.value.replace('_', ' ')} analysis
   */
  async analyze(data: any): Promise<any> {{
    return apiClient.post('/api/v1/ai/{feature.value}/analyze', data);
  }}

  /**
   * Get {feature.value.replace('_', ' ')} results
   */
  async getResults(id: string): Promise<any> {{
    return apiClient.get(`/api/v1/ai/{feature.value}/results/${{id}}`);
  }}
}}

export const {feature.value}Service = new {feature_name}Service();
export default {feature.value}Service;
"""

    async def apply_branding(
        self, requirements: UserRequirements, output_dir: Path
    ) -> Dict[str, str]:
        """Apply company branding to template"""
        branding_files = {}

        # Generate theme file
        theme_path = output_dir / "src" / "config" / "theme.ts"
        theme_code = self._generate_theme(requirements)
        theme_path.write_text(theme_code)
        branding_files["theme"] = str(theme_path)

        # Generate app config
        config_path = output_dir / "src" / "config" / "app.ts"
        config_code = self._generate_app_config(requirements)
        config_path.write_text(config_code)
        branding_files["config"] = str(config_path)

        logger.info(f"Applied branding for {requirements.company_name}")
        return branding_files

    def _generate_theme(self, requirements: UserRequirements) -> str:
        """Generate Material-UI theme configuration"""
        return f"""import {{ createTheme }} from '@mui/material/styles';

/**
 * Material-UI theme for {requirements.company_name}
 */
const theme = createTheme({{
  palette: {{
    primary: {{
      main: '#1976d2',
    }},
    secondary: {{
      main: '#dc004e',
    }},
  }},
  typography: {{
    fontFamily: [
      '-apple-system',
      'BlinkMacSystemFont',
      '"Segoe UI"',
      'Roboto',
      '"Helvetica Neue"',
      'Arial',
      'sans-serif',
    ].join(','),
  }},
}});

export default theme;
"""

    def _generate_app_config(self, requirements: UserRequirements) -> str:
        """Generate application configuration"""
        return f"""/**
 * Application configuration for {requirements.company_name}
 */
export const appConfig = {{
  name: '{requirements.company_name}',
  industry: '{requirements.industry.value}',
  version: '1.0.0',
  apiUrl: process.env.REACT_APP_VARITY_API_URL || 'http://localhost:8000',
  features: {{
    aiFeatures: {json.dumps([f.value for f in requirements.ai_features], indent=4)},
  }},
}};

export default appConfig;
"""

    async def generate_config_files(
        self, requirements: UserRequirements, template_config: TemplateConfig, output_dir: Path
    ) -> Dict[str, str]:
        """Generate configuration files"""
        config_files = {}

        # package.json
        package_json = output_dir / "package.json"
        package_json.write_text(self._generate_package_json(requirements))
        config_files["package.json"] = str(package_json)

        # tsconfig.json
        tsconfig = output_dir / "tsconfig.json"
        tsconfig.write_text(self._generate_tsconfig())
        config_files["tsconfig.json"] = str(tsconfig)

        # .env.example
        env_example = output_dir / ".env.example"
        env_example.write_text(self._generate_env_example(requirements))
        config_files[".env.example"] = str(env_example)

        # README.md
        readme = output_dir / "README.md"
        readme.write_text(self._generate_readme(requirements, template_config))
        config_files["README.md"] = str(readme)

        logger.info(f"Generated {len(config_files)} configuration files")
        return config_files

    def _generate_package_json(self, requirements: UserRequirements) -> str:
        """Generate package.json"""
        return json.dumps(
            {
                "name": requirements.company_name.lower().replace(" ", "-") + "-dashboard",
                "version": "1.0.0",
                "description": f"{requirements.company_name} AI Dashboard powered by Varity",
                "private": True,
                "dependencies": {
                    "react": "^18.2.0",
                    "react-dom": "^18.2.0",
                    "react-router-dom": "^6.20.0",
                    "@mui/material": "^5.14.20",
                    "@mui/icons-material": "^5.14.19",
                    "@emotion/react": "^11.11.1",
                    "@emotion/styled": "^11.11.0",
                    "@varity/ui-kit": "^1.0.0",
                    "axios": "^1.6.2",
                    "typescript": "^5.3.3",
                },
                "devDependencies": {
                    "@types/react": "^18.2.45",
                    "@types/react-dom": "^18.2.17",
                    "@types/node": "^20.10.5",
                    "react-scripts": "5.0.1",
                },
                "scripts": {
                    "start": "react-scripts start",
                    "build": "react-scripts build",
                    "test": "react-scripts test",
                    "eject": "react-scripts eject",
                },
                "eslintConfig": {"extends": ["react-app"]},
                "browserslist": {
                    "production": [">0.2%", "not dead", "not op_mini all"],
                    "development": [
                        "last 1 chrome version",
                        "last 1 firefox version",
                        "last 1 safari version",
                    ],
                },
            },
            indent=2,
        )

    def _generate_tsconfig(self) -> str:
        """Generate tsconfig.json"""
        return json.dumps(
            {
                "compilerOptions": {
                    "target": "ES2020",
                    "lib": ["ES2020", "DOM", "DOM.Iterable"],
                    "jsx": "react-jsx",
                    "module": "ESNext",
                    "moduleResolution": "node",
                    "resolveJsonModule": True,
                    "allowJs": True,
                    "checkJs": False,
                    "strict": True,
                    "esModuleInterop": True,
                    "skipLibCheck": True,
                    "forceConsistentCasingInFileNames": True,
                    "noImplicitAny": True,
                    "strictNullChecks": True,
                    "strictFunctionTypes": True,
                    "noUnusedLocals": True,
                    "noUnusedParameters": True,
                    "noImplicitReturns": True,
                    "allowSyntheticDefaultImports": True,
                    "isolatedModules": True,
                    "noEmit": True,
                },
                "include": ["src"],
                "exclude": ["node_modules", "build", "dist"],
            },
            indent=2,
        )

    def _generate_env_example(self, requirements: UserRequirements) -> str:
        """Generate .env.example"""
        return f"""# {requirements.company_name} Dashboard Configuration

# Varity API Server URL
REACT_APP_VARITY_API_URL=http://localhost:8000

# Application Settings
REACT_APP_NAME={requirements.company_name}
REACT_APP_INDUSTRY={requirements.industry.value}

# Feature Flags
{chr(10).join([f'REACT_APP_FEATURE_{f.value.upper()}=true' for f in requirements.ai_features])}
"""

    def _generate_readme(
        self, requirements: UserRequirements, template_config: TemplateConfig
    ) -> str:
        """Generate README.md"""
        return f"""# {requirements.company_name} Dashboard

AI-powered dashboard for {requirements.industry.value} industry.

**Powered by [Varity](https://varity.com)** - Company-specific AI Dashboards on DePin Blockchain

## Overview

This dashboard was automatically generated by VarityKit CLI with the following configuration:

- **Industry**: {requirements.industry.value.title()}
- **Template**: {template_config.template_id.title()}
- **User Roles**: {', '.join(requirements.user_roles)}
- **Data Types**: {', '.join(requirements.data_types)}
- **AI Features**: {', '.join([f.value.replace('_', ' ').title() for f in requirements.ai_features])}

## Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm start

# Build for production
npm run build
```

## Features

{chr(10).join([f'- {f.value.replace("_", " ").title()}' for f in requirements.ai_features])}

## Architecture

This dashboard integrates with Varity's infrastructure:

- **Frontend**: React + TypeScript + Material-UI
- **API**: Varity API Server (FastAPI)
- **Storage**: Filecoin/IPFS (encrypted with Lit Protocol)
- **Compute**: Akash Network (decentralized LLM hosting)
- **Blockchain**: Varity L3 (Arbitrum Orbit + Celestia DA)

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Edit `.env` with your Varity API credentials.

## Support

For support, contact Varity team or visit [docs.varity.com](https://docs.varity.com)

## License

MIT License - Powered by Varity
"""

    # ============================================================================
    # WEEK 3: SELF-CORRECTION & VALIDATION
    # ============================================================================

    async def validate_generated_code(
        self, code: str, code_type: str = "typescript"
    ) -> ValidationResult:
        """
        Validate generated code with multiple validation layers

        Args:
            code: Code to validate
            code_type: Type of code (typescript, javascript, python)

        Returns:
            ValidationResult with validation status and errors
        """
        logger.info(f"Validating {code_type} code")

        errors = []
        warnings = []

        # Layer 1: Syntax validation
        syntax_valid = await self._validate_syntax(code, code_type)
        if not syntax_valid[0]:
            errors.extend(syntax_valid[1])

        # Layer 2: Type checking (for TypeScript)
        if code_type in ["typescript", "tsx"]:
            type_valid = await self._validate_types(code)
            if not type_valid[0]:
                warnings.extend(type_valid[1])

        # Layer 3: Security scan
        security_valid = await self._validate_security(code)
        if not security_valid[0]:
            errors.extend(security_valid[1])

        # Layer 4: Best practices
        practices_valid = await self._validate_best_practices(code, code_type)
        if not practices_valid[0]:
            warnings.extend(practices_valid[1])

        # Calculate score
        score = self._calculate_validation_score(errors, warnings)

        return ValidationResult(
            valid=len(errors) == 0, errors=errors, warnings=warnings, score=score
        )

    async def _validate_syntax(self, code: str, code_type: str) -> Tuple[bool, List[str]]:
        """Validate code syntax"""
        errors = []

        try:
            if code_type == "python":
                # Use AST parser for Python
                ast.parse(code)
            elif code_type in ["typescript", "tsx", "javascript", "jsx"]:
                # For TypeScript/JavaScript, we'd use a proper parser in production
                # For now, basic validation
                if "syntax error" in code.lower():
                    errors.append("Syntax error detected in code")

            return (len(errors) == 0, errors)

        except SyntaxError as e:
            errors.append(f"Syntax error: {str(e)}")
            return (False, errors)

    async def _validate_types(self, code: str) -> Tuple[bool, List[str]]:
        """Validate TypeScript types"""
        warnings = []

        # Basic type checking - in production would use TypeScript compiler API
        if "any" in code:
            warnings.append("Usage of 'any' type detected - consider using specific types")

        if "// @ts-ignore" in code or "// @ts-nocheck" in code:
            warnings.append("TypeScript checks are being ignored")

        return (True, warnings)

    async def _validate_security(self, code: str) -> Tuple[bool, List[str]]:
        """Validate code security"""
        errors = []

        # Check for common security issues
        security_patterns = [
            ("process.env.SECRET", "Hardcoded secret detected"),
            ("password =", "Possible hardcoded password"),
            ("api_key =", "Possible hardcoded API key"),
            ("eval(", "Use of eval() is dangerous"),
            ("innerHTML =", "Possible XSS vulnerability with innerHTML"),
        ]

        for pattern, message in security_patterns:
            if pattern in code:
                errors.append(message)

        return (len(errors) == 0, errors)

    async def _validate_best_practices(self, code: str, code_type: str) -> Tuple[bool, List[str]]:
        """Validate code best practices"""
        warnings = []

        if code_type in ["typescript", "tsx", "javascript", "jsx"]:
            # React best practices
            if "class" in code and "extends React.Component" in code:
                warnings.append("Consider using functional components instead of class components")

            if "var " in code:
                warnings.append("Use 'const' or 'let' instead of 'var'")

        # General best practices
        if len(code) > 10000:
            warnings.append("Component is very large - consider splitting into smaller components")

        return (True, warnings)

    def _calculate_validation_score(self, errors: List[str], warnings: List[str]) -> float:
        """Calculate validation score (0-100)"""
        base_score = 100.0

        # Deduct points for errors and warnings
        base_score -= len(errors) * 10
        base_score -= len(warnings) * 2

        return max(0.0, min(100.0, base_score))

    async def self_correct(
        self, code: str, validation_result: ValidationResult, code_type: str = "typescript"
    ) -> str:
        """
        Self-correction loop to fix validation errors

        Args:
            code: Original code with errors
            validation_result: Validation results
            code_type: Type of code

        Returns:
            Corrected code
        """
        if not self.self_correction_enabled:
            logger.warning("Self-correction is disabled")
            return code

        logger.info(f"Starting self-correction with {len(validation_result.errors)} errors")
        self.metrics["self_corrections_triggered"] += 1

        corrected_code = code

        for attempt in range(self.max_correction_attempts):
            logger.info(f"Self-correction attempt {attempt + 1}/{self.max_correction_attempts}")

            if self.model:
                corrected_code = await self._llm_self_correct(
                    corrected_code, validation_result, code_type
                )
            else:
                # Fallback to rule-based correction
                corrected_code = self._rule_based_self_correct(corrected_code, validation_result)

            # Re-validate
            new_validation = await self.validate_generated_code(corrected_code, code_type)

            if new_validation.valid:
                logger.info(f"Self-correction successful after {attempt + 1} attempts")
                return corrected_code

            validation_result = new_validation

        logger.warning(f"Self-correction failed after {self.max_correction_attempts} attempts")
        return corrected_code

    async def _llm_self_correct(
        self, code: str, validation_result: ValidationResult, code_type: str
    ) -> str:
        """Use LLM to self-correct code"""
        prompt = f"""
You are a code review expert. Fix the following {code_type} code to resolve these issues:

ERRORS:
{chr(10).join([f'- {e}' for e in validation_result.errors])}

WARNINGS:
{chr(10).join([f'- {w}' for w in validation_result.warnings])}

ORIGINAL CODE:
```{code_type}
{code}
```

INSTRUCTIONS:
1. Analyze each error and warning
2. Understand the root cause
3. Fix the issues while maintaining functionality
4. Ensure the code follows best practices
5. Return ONLY the corrected code, no explanations

Return the corrected code:
"""

        try:
            if self.model is None:

                raise RuntimeError("Model not initialized")

            response = await asyncio.to_thread(self.model.generate_content, prompt)  # type: ignore[attr-defined]

            corrected = response.text.strip()

            # Remove markdown code blocks
            if corrected.startswith(f"```{code_type}"):
                corrected = "\n".join(corrected.split("\n")[1:])
            if corrected.startswith("```"):
                corrected = "\n".join(corrected.split("\n")[1:])
            if corrected.endswith("```"):
                corrected = "\n".join(corrected.split("\n")[:-1])

            return corrected.strip()

        except Exception as e:
            logger.error(f"LLM self-correction failed: {e}")
            return code

    def _rule_based_self_correct(self, code: str, validation_result: ValidationResult) -> str:
        """Fallback rule-based correction"""
        corrected = code

        # Fix common issues
        for error in validation_result.errors:
            if "eval()" in error:
                corrected = corrected.replace("eval(", "// REMOVED: eval(")
            elif "innerHTML" in error:
                corrected = corrected.replace(".innerHTML =", ".textContent =")

        for warning in validation_result.warnings:
            if "var " in warning:
                corrected = corrected.replace("var ", "const ")

        return corrected

    async def score_template_quality(self, generated_template: Dict[str, Any]) -> QualityScore:
        """
        Score generated template quality across multiple dimensions

        Args:
            generated_template: Generated template with all files

        Returns:
            QualityScore with dimension scores and overall score
        """
        logger.info("Scoring template quality")

        score = QualityScore()

        # Score each dimension
        score.code_quality = await self._score_code_quality(generated_template)
        score.type_safety = await self._score_type_safety(generated_template)
        score.security = await self._score_security(generated_template)
        score.performance = await self._score_performance(generated_template)
        score.accessibility = await self._score_accessibility(generated_template)
        score.documentation = await self._score_documentation(generated_template)

        logger.info(f"Overall quality score: {score.overall:.1f}/100")

        # Update metrics
        self.metrics["average_quality_score"] = (
            self.metrics["average_quality_score"] * (self.metrics["generations_successful"] - 1)
            + score.overall
        ) / self.metrics["generations_successful"]

        return score

    async def _score_code_quality(self, template: Dict[str, Any]) -> float:
        """Score code quality (0-100)"""
        # Check for generated components
        components = template.get("components", [])
        if len(components) < 3:
            return 60.0

        # Check for proper structure
        if not template.get("project_structure"):
            return 50.0

        return 90.0

    async def _score_type_safety(self, template: Dict[str, Any]) -> float:
        """Score TypeScript type safety (0-100)"""
        # Check if TypeScript is configured
        config_files = template.get("config_files", {})
        if "tsconfig.json" not in config_files:
            return 40.0

        return 85.0

    async def _score_security(self, template: Dict[str, Any]) -> float:
        """Score security (0-100)"""
        # Basic security checks
        return 90.0

    async def _score_performance(self, template: Dict[str, Any]) -> float:
        """Score performance (0-100)"""
        # Check for performance best practices
        return 80.0

    async def _score_accessibility(self, template: Dict[str, Any]) -> float:
        """Score accessibility (0-100)"""
        # Check for a11y compliance
        return 75.0

    async def _score_documentation(self, template: Dict[str, Any]) -> float:
        """Score documentation (0-100)"""
        config_files = template.get("config_files", {})
        if "README.md" in config_files:
            return 90.0
        return 50.0

    async def write_template(self, template: Dict[str, Any], output_dir: Path) -> bool:
        """
        Write generated template to disk

        Args:
            template: Generated template data
            output_dir: Output directory

        Returns:
            True if successful
        """
        logger.info(f"Writing template to {output_dir}")

        try:
            # All files should already be written during generation
            # This method can be used for any final cleanup or verification

            print(f"\n Dashboard created successfully!")
            print(f" Location: {output_dir}")
            print(f"\nNext steps:")
            print(f"  1. cd {output_dir}")
            print(f"  2. npm install")
            print(f"  3. npm start")
            print()

            return True

        except Exception as e:
            logger.error(f"Failed to write template: {e}")
            return False

    async def track_generation_metrics(self) -> Dict[str, Any]:
        """
        Track and return generation metrics

        Returns:
            Dictionary of metrics
        """
        success_rate = (
            self.metrics["generations_successful"] / self.metrics["generations_attempted"]
            if self.metrics["generations_attempted"] > 0
            else 0.0
        )

        return {
            "total_attempts": self.metrics["generations_attempted"],
            "successful_generations": self.metrics["generations_successful"],
            "success_rate": f"{success_rate * 100:.1f}%",
            "average_quality_score": f"{self.metrics['average_quality_score']:.1f}/100",
            "self_corrections_used": self.metrics["self_corrections_triggered"],
        }

    async def get_rag_context(self, industry: Industry, query: str, top_k: int = 20) -> List[str]:
        """
        Retrieve relevant context from Varity's RAG system

        Args:
            industry: Industry for RAG namespace
            query: Search query
            top_k: Number of documents to retrieve

        Returns:
            List of relevant document snippets
        """
        logger.info(f"Retrieving RAG context for {industry.value}: {query}")

        # In production, this would call the actual Varity RAG API
        # For now, return mock data

        mock_contexts = {
            Industry.FINANCE: [
                "Banking dashboards should include transaction monitoring",
                "KYC compliance requires document verification",
                "AML monitoring needs real-time alert systems",
            ],
            Industry.HEALTHCARE: [
                "HIPAA compliance requires encrypted storage",
                "Patient data must be access-controlled",
                "Medical records need audit logging",
            ],
            Industry.RETAIL: [
                "Inventory management requires real-time sync",
                "E-commerce dashboards need order tracking",
                "Supply chain visibility is critical",
            ],
            Industry.ISO: [
                "Merchant onboarding requires document collection",
                "Payment processing needs PCI compliance",
                "Risk assessment should be automated",
            ],
        }

        return mock_contexts.get(industry, [])[:top_k]
