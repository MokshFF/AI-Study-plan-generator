"""AI-Powered Personalized Study Plan Generator using Local Ollama Models.
Problem ID: C20 - Bennett University Prompt Engineering Mini-Project
"""

from study_plan.fixtures import get_sample_input
from study_plan.ollama_client import call_ollama_study_planner, check_ollama_status
from study_plan.prompt_template import PROMPT_VERSIONS, build_study_plan_prompt
from study_plan.validator import StudyPlanInput, SubjectInput, validate_inputs, validate_plan_output

__version__ = "2.0.0"
