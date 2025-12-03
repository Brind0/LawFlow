import yaml
from pathlib import Path
from typing import List, Dict, Optional
from jinja2 import Template, TemplateError
from database.models import Stage, ContentType


class PromptService:
    """
    Service layer for loading and rendering prompt templates.
    Handles YAML template loading, Jinja2 rendering, and template caching.
    """

    def __init__(self):
        """Initialize the service with template caching."""
        self.template_cache: Dict[Stage, Dict] = {}
        self._load_templates()

    def _load_templates(self) -> None:
        """
        Load all YAML templates from config/prompts/ directory.
        Templates are cached in memory for performance.
        """
        # Get the base directory (project root)
        base_dir = Path(__file__).parent.parent
        prompts_dir = base_dir / "config" / "prompts"

        # Load each template
        template_files = {
            Stage.MK1: "mk1_template.yaml",
            Stage.MK2: "mk2_template.yaml",
            Stage.MK3: "mk3_template.yaml"
        }

        for stage, filename in template_files.items():
            template_path = prompts_dir / filename

            if not template_path.exists():
                raise FileNotFoundError(
                    f"Template file not found: {template_path}"
                )

            with open(template_path, 'r', encoding='utf-8') as f:
                template_data = yaml.safe_load(f)

            # Validate template structure
            if not all(key in template_data for key in ['name', 'description', 'template']):
                raise ValueError(
                    f"Invalid template structure in {filename}. "
                    f"Must contain 'name', 'description', and 'template' keys."
                )

            # Cache the template data
            self.template_cache[stage] = template_data

    def build_prompt(
        self,
        stage: Stage,
        topic_name: str,
        module_name: str,
        file_names: List[str],
        previous_content: Optional[str] = None
    ) -> str:
        """
        Build a complete prompt for a given generation stage.

        Args:
            stage: The generation stage (MK1, MK2, or MK3)
            topic_name: Name of the topic (e.g., "Easements")
            module_name: Name of the module (e.g., "Land Law")
            file_names: List of uploaded file names
            previous_content: Optional - for MK3, includes MK2 content

        Returns:
            Fully rendered prompt string ready to copy-paste to Claude

        Raises:
            ValueError: If stage is not recognized or required variables are missing
            TemplateError: If Jinja2 rendering fails
        """
        # Validate stage
        if stage not in self.template_cache:
            raise ValueError(f"Unknown stage: {stage}")

        # Get cached template
        template_data = self.template_cache[stage]
        template_string = template_data['template']

        # Prepare template variables
        template_vars = {
            'topic_name': topic_name,
            'module_name': module_name,
            'files': file_names
        }

        # Add previous_content for MK3
        if stage == Stage.MK3:
            if previous_content is None:
                raise ValueError(
                    "MK3 requires previous_content (MK2 output) to be provided"
                )
            template_vars['previous_content'] = previous_content

        # Render template with Jinja2
        try:
            jinja_template = Template(template_string)
            rendered_prompt = jinja_template.render(**template_vars)
            return rendered_prompt
        except TemplateError as e:
            raise TemplateError(
                f"Failed to render template for {stage.value}: {str(e)}"
            )

    def get_required_files_for_stage(self, stage: Stage) -> List[ContentType]:
        """
        Get the required file types for each generation stage.
        Helper method for validation.

        Args:
            stage: The generation stage

        Returns:
            List of required ContentType values

        Raises:
            ValueError: If stage is not recognized
        """
        requirements = {
            Stage.MK1: [
                ContentType.LECTURE_PDF
            ],
            Stage.MK2: [
                ContentType.LECTURE_PDF,
                ContentType.SOURCE_MATERIAL,
                ContentType.TUTORIAL_PDF
            ],
            Stage.MK3: [
                ContentType.LECTURE_PDF,
                ContentType.SOURCE_MATERIAL,
                ContentType.TUTORIAL_PDF,
                ContentType.TRANSCRIPT
            ]
        }

        if stage not in requirements:
            raise ValueError(f"Unknown stage: {stage}")

        return requirements[stage]

    def get_template_info(self, stage: Stage) -> Dict[str, str]:
        """
        Get metadata about a template.

        Args:
            stage: The generation stage

        Returns:
            Dictionary with 'name' and 'description' keys

        Raises:
            ValueError: If stage is not recognized
        """
        if stage not in self.template_cache:
            raise ValueError(f"Unknown stage: {stage}")

        template_data = self.template_cache[stage]
        return {
            'name': template_data['name'],
            'description': template_data['description']
        }
