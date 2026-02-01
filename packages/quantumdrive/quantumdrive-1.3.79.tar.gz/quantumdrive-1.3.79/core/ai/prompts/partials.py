from typing import Any
from jinja2 import Template

from .thought_process import THOUGHT_PROCESS
from .default_system_role import DEFAULT_SYSTEM_ROLE
from .chain_of_thought import CHAIN_OF_THOUGHT
from .few_shot import FEW_SHOT_EXAMPLES
from .role_playing import ROLE_DEFINITION
from .output_constraints import OUTPUT_CONSTRAINTS
from .reflection import REFLECTION_CORRECTION
from .context_fidelity import CONTEXT_FIDELITY
from .step_back import STEP_BACK
from .threat_modeling import THREAT_MODELING
from .gov_compliance import GOV_COMPLIANCE_CITATION
from .evaluation_scoring import EVALUATION_SCORING
from .clin_structure import CLIN_STRUCTURE
from .past_performance import PAST_PERFORMANCE
from .red_team_gov import RED_TEAM_GOV
from .solicitation_sections import SOLICITATION_SECTIONS
from .tool_execution import TOOL_EXECUTION_PREAMBLE


class PromptPartials:
    """
    Reusable static prompt components.
    """
    # -------------------------------------------------------------------------
    # Core
    # -------------------------------------------------------------------------
    DEFAULT_SYSTEM_ROLE = DEFAULT_SYSTEM_ROLE
    # TOOL_EXECUTION = TOOL_EXECUTION_PREAMBLE
    
    # -------------------------------------------------------------------------
    # Reasoning Patterns
    # -------------------------------------------------------------------------
    THOUGHT_PROCESS = THOUGHT_PROCESS  # Legacy simple version
    CHAIN_OF_THOUGHT = CHAIN_OF_THOUGHT  # Detailed version
    REFLECTION = REFLECTION_CORRECTION
    STEP_BACK = STEP_BACK
    THREAT_MODELING = THREAT_MODELING
    
    # -------------------------------------------------------------------------
    # GovCon Domain Specific
    # -------------------------------------------------------------------------
    GOV_COMPLIANCE = GOV_COMPLIANCE_CITATION
    EVALUATION_SCORING = EVALUATION_SCORING
    CLIN_STRUCTURE = CLIN_STRUCTURE
    PAST_PERFORMANCE = PAST_PERFORMANCE
    RED_TEAM_GOV = RED_TEAM_GOV
    SOLICITATION_SECTIONS = SOLICITATION_SECTIONS

    # -------------------------------------------------------------------------
    # Structure & Context Patterns
    # -------------------------------------------------------------------------
    FEW_SHOT = FEW_SHOT_EXAMPLES
    ROLE_PLAYING = ROLE_DEFINITION
    CONTEXT_FIDELITY = CONTEXT_FIDELITY
    
    # -------------------------------------------------------------------------
    # Formatting
    # -------------------------------------------------------------------------
    # JSON_RESPONSE_FORMAT removed as it is handled by OUTPUT_CONSTRAINTS
    OUTPUT_CONSTRAINTS = OUTPUT_CONSTRAINTS # Generic version
