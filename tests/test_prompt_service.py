"""
Unit tests for PromptService.

Tests template loading, Jinja2 rendering, and prompt generation
for all three stages (MK1, MK2, MK3).
"""
import pytest
from pathlib import Path
from services.prompt_service import PromptService
from database.models import Stage, ContentType
from jinja2 import TemplateError


class TestPromptService:
    """Test suite for PromptService"""

    @pytest.fixture
    def service(self):
        """Create a PromptService instance"""
        return PromptService()

    # ==================== TEMPLATE LOADING TESTS ====================

    def test_service_initialization_loads_templates(self, service):
        """Test that service loads all templates on initialization"""
        assert len(service.template_cache) == 3
        assert Stage.MK1 in service.template_cache
        assert Stage.MK2 in service.template_cache
        assert Stage.MK3 in service.template_cache

    def test_template_cache_structure(self, service):
        """Test that cached templates have the correct structure"""
        for stage in [Stage.MK1, Stage.MK2, Stage.MK3]:
            template_data = service.template_cache[stage]
            assert 'name' in template_data
            assert 'description' in template_data
            assert 'template' in template_data
            assert isinstance(template_data['name'], str)
            assert isinstance(template_data['description'], str)
            assert isinstance(template_data['template'], str)

    def test_template_names_are_correct(self, service):
        """Test that template names match expected values"""
        mk1_name = service.template_cache[Stage.MK1]['name']
        mk2_name = service.template_cache[Stage.MK2]['name']
        mk3_name = service.template_cache[Stage.MK3]['name']

        assert "Mk-1" in mk1_name or "MK1" in mk1_name.upper()
        assert "Mk-2" in mk2_name or "MK2" in mk2_name.upper()
        assert "Mk-3" in mk3_name or "MK3" in mk3_name.upper()

    # ==================== PROMPT BUILDING TESTS ====================

    def test_build_prompt_mk1_basic(self, service):
        """Test building MK1 prompt with basic inputs"""
        prompt = service.build_prompt(
            stage=Stage.MK1,
            topic_name="Easements",
            module_name="Land Law",
            file_names=["lecture_easements.pdf"]
        )

        assert prompt is not None
        assert isinstance(prompt, str)
        assert "Easements" in prompt
        assert "Land Law" in prompt
        assert "lecture_easements.pdf" in prompt

    def test_build_prompt_mk1_multiple_files(self, service):
        """Test building MK1 prompt with multiple files (edge case)"""
        prompt = service.build_prompt(
            stage=Stage.MK1,
            topic_name="Negligence",
            module_name="Tort Law",
            file_names=[
                "lecture_negligence.pdf",
                "lecture_duty_of_care.pdf"
            ]
        )

        assert "lecture_negligence.pdf" in prompt
        assert "lecture_duty_of_care.pdf" in prompt

    def test_build_prompt_mk2_basic(self, service):
        """Test building MK2 prompt with all required files"""
        prompt = service.build_prompt(
            stage=Stage.MK2,
            topic_name="Contract Formation",
            module_name="Contract Law",
            file_names=[
                "lecture_formation.pdf",
                "sources_contract_act.pdf",
                "tutorial_questions.pdf"
            ]
        )

        assert "Contract Formation" in prompt
        assert "Contract Law" in prompt
        assert "lecture_formation.pdf" in prompt
        assert "sources_contract_act.pdf" in prompt
        assert "tutorial_questions.pdf" in prompt

    def test_build_prompt_mk3_with_previous_content(self, service):
        """Test building MK3 prompt with previous MK2 content"""
        previous_mk2_content = """
        # Contract Formation - MK2 Notes
        ## Key Concepts
        - Offer and Acceptance
        - Consideration
        """

        prompt = service.build_prompt(
            stage=Stage.MK3,
            topic_name="Contract Formation",
            module_name="Contract Law",
            file_names=[
                "lecture_formation.pdf",
                "sources_contract_act.pdf",
                "tutorial_questions.pdf",
                "transcript_lecture.txt"
            ],
            previous_content=previous_mk2_content
        )

        assert "Contract Formation" in prompt
        assert previous_mk2_content in prompt
        assert "transcript_lecture.txt" in prompt

    def test_build_prompt_mk3_without_previous_content_raises_error(self, service):
        """Test that MK3 requires previous_content"""
        with pytest.raises(ValueError, match="MK3 requires previous_content"):
            service.build_prompt(
                stage=Stage.MK3,
                topic_name="Topic",
                module_name="Module",
                file_names=["file.pdf"]
            )

    def test_build_prompt_mk1_mk2_ignore_previous_content(self, service):
        """Test that MK1 and MK2 work fine even if previous_content is provided"""
        # Should not raise error, just ignore the parameter
        prompt_mk1 = service.build_prompt(
            stage=Stage.MK1,
            topic_name="Topic",
            module_name="Module",
            file_names=["file.pdf"],
            previous_content="This should be ignored"
        )

        prompt_mk2 = service.build_prompt(
            stage=Stage.MK2,
            topic_name="Topic",
            module_name="Module",
            file_names=["file1.pdf", "file2.pdf"],
            previous_content="This should also be ignored"
        )

        assert prompt_mk1 is not None
        assert prompt_mk2 is not None

    def test_build_prompt_invalid_stage_raises_error(self, service):
        """Test that invalid stage raises ValueError"""
        # This should never happen in practice, but test defensively
        with pytest.raises((ValueError, KeyError)):
            service.build_prompt(
                stage="INVALID_STAGE",
                topic_name="Topic",
                module_name="Module",
                file_names=["file.pdf"]
            )

    def test_build_prompt_with_special_characters(self, service):
        """Test prompt building with special characters in names"""
        prompt = service.build_prompt(
            stage=Stage.MK1,
            topic_name="Co-ownership & Trusts",
            module_name="Land Law (2024/25)",
            file_names=["lecture_co-ownership_&_trusts.pdf"]
        )

        assert "Co-ownership & Trusts" in prompt
        assert "Land Law (2024/25)" in prompt

    def test_build_prompt_with_empty_file_list(self, service):
        """Test prompt building with empty file list"""
        prompt = service.build_prompt(
            stage=Stage.MK1,
            topic_name="Topic",
            module_name="Module",
            file_names=[]
        )

        # Should still work, just no files listed
        assert prompt is not None
        assert "Topic" in prompt
        assert "Module" in prompt

    # ==================== JINJA2 VARIABLE TESTS ====================

    def test_jinja2_variables_are_substituted(self, service):
        """Test that all Jinja2 variables are properly substituted"""
        prompt = service.build_prompt(
            stage=Stage.MK1,
            topic_name="TestTopic",
            module_name="TestModule",
            file_names=["test_file.pdf"]
        )

        # Should not contain any Jinja2 template syntax
        assert "{{" not in prompt
        assert "}}" not in prompt
        assert "{%" not in prompt
        assert "%}" not in prompt

    def test_jinja2_for_loop_renders_all_files(self, service):
        """Test that Jinja2 for loop renders all files in the list"""
        files = ["file1.pdf", "file2.pdf", "file3.pdf"]
        prompt = service.build_prompt(
            stage=Stage.MK2,
            topic_name="Topic",
            module_name="Module",
            file_names=files
        )

        for file_name in files:
            assert file_name in prompt

    # ==================== GET REQUIRED FILES TESTS ====================

    def test_get_required_files_mk1(self, service):
        """Test required files for MK1 stage"""
        required = service.get_required_files_for_stage(Stage.MK1)

        assert len(required) == 1
        assert ContentType.LECTURE_PDF in required

    def test_get_required_files_mk2(self, service):
        """Test required files for MK2 stage"""
        required = service.get_required_files_for_stage(Stage.MK2)

        assert len(required) == 3
        assert ContentType.LECTURE_PDF in required
        assert ContentType.SOURCE_MATERIAL in required
        assert ContentType.TUTORIAL_PDF in required

    def test_get_required_files_mk3(self, service):
        """Test required files for MK3 stage"""
        required = service.get_required_files_for_stage(Stage.MK3)

        assert len(required) == 4
        assert ContentType.LECTURE_PDF in required
        assert ContentType.SOURCE_MATERIAL in required
        assert ContentType.TUTORIAL_PDF in required
        assert ContentType.TRANSCRIPT in required

    def test_get_required_files_invalid_stage_raises_error(self, service):
        """Test that invalid stage raises ValueError"""
        with pytest.raises(ValueError, match="Unknown stage"):
            service.get_required_files_for_stage("INVALID_STAGE")

    # ==================== GET TEMPLATE INFO TESTS ====================

    def test_get_template_info_mk1(self, service):
        """Test getting template metadata for MK1"""
        info = service.get_template_info(Stage.MK1)

        assert 'name' in info
        assert 'description' in info
        assert isinstance(info['name'], str)
        assert isinstance(info['description'], str)
        assert len(info['name']) > 0
        assert len(info['description']) > 0

    def test_get_template_info_all_stages(self, service):
        """Test getting template metadata for all stages"""
        for stage in [Stage.MK1, Stage.MK2, Stage.MK3]:
            info = service.get_template_info(stage)
            assert 'name' in info
            assert 'description' in info

    def test_get_template_info_invalid_stage_raises_error(self, service):
        """Test that invalid stage raises ValueError"""
        with pytest.raises(ValueError, match="Unknown stage"):
            service.get_template_info("INVALID_STAGE")

    # ==================== TEMPLATE CACHING TESTS ====================

    def test_template_caching_performance(self, service):
        """Test that templates are cached and not reloaded on each call"""
        # Get the initial cache reference
        initial_cache = service.template_cache

        # Build multiple prompts
        for _ in range(5):
            service.build_prompt(
                stage=Stage.MK1,
                topic_name="Topic",
                module_name="Module",
                file_names=["file.pdf"]
            )

        # Cache should be the same object (not reloaded)
        assert service.template_cache is initial_cache

    # ==================== INTEGRATION TESTS ====================

    def test_full_workflow_mk1_to_mk3(self, service):
        """Test complete workflow building prompts for all three stages"""
        topic = "Easements"
        module = "Land Law"

        # Stage 1: MK1
        mk1_prompt = service.build_prompt(
            stage=Stage.MK1,
            topic_name=topic,
            module_name=module,
            file_names=["lecture_easements.pdf"]
        )
        assert topic in mk1_prompt

        # Stage 2: MK2
        mk2_prompt = service.build_prompt(
            stage=Stage.MK2,
            topic_name=topic,
            module_name=module,
            file_names=[
                "lecture_easements.pdf",
                "source_lra_2002.pdf",
                "tutorial_questions.pdf"
            ]
        )
        assert topic in mk2_prompt

        # Stage 3: MK3 (with previous MK2 content)
        mk2_response = "# Easements - Detailed Notes\n## Legal Definition\n..."
        mk3_prompt = service.build_prompt(
            stage=Stage.MK3,
            topic_name=topic,
            module_name=module,
            file_names=[
                "lecture_easements.pdf",
                "source_lra_2002.pdf",
                "tutorial_questions.pdf",
                "transcript_lecture.txt"
            ],
            previous_content=mk2_response
        )
        assert topic in mk3_prompt
        assert mk2_response in mk3_prompt

    def test_prompt_output_format(self, service):
        """Test that generated prompts are properly formatted"""
        prompt = service.build_prompt(
            stage=Stage.MK1,
            topic_name="Test Topic",
            module_name="Test Module",
            file_names=["test.pdf"]
        )

        # Should be a non-empty string
        assert isinstance(prompt, str)
        assert len(prompt) > 0

        # Should contain some markdown structure (headers)
        assert "#" in prompt

        # Should not be just whitespace
        assert prompt.strip() != ""

    def test_consistent_prompt_generation(self, service):
        """Test that generating the same prompt twice yields identical results"""
        params = {
            "stage": Stage.MK1,
            "topic_name": "Test",
            "module_name": "Module",
            "file_names": ["file.pdf"]
        }

        prompt1 = service.build_prompt(**params)
        prompt2 = service.build_prompt(**params)

        assert prompt1 == prompt2
