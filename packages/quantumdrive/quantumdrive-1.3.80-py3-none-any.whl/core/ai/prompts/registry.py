import logging
from typing import Dict, Any
from . import PromptLibrary, PromptPartials

logger = logging.getLogger(__name__)


class PromptRegistry:
    """
    Central registry for pre-configured, named prompts within the QuantumDrive framework.
    This allows applications (like Quantify) to retrieve standard, optimized prompts by name.
    """

    _REGISTRY: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def register(cls, name: str, build_params: Dict[str, Any]) -> None:
        """
        Register a prompt configuration under a specific name.
        
        Args:
            name: The unique identifier for the prompt (e.g., 'solicitation_ingestion').
            build_params: A dictionary of parameters to pass to PromptLibrary.build().
                          Templates (like schemas) can be left as placeholders to be filled at runtime.
        """
        if name in cls._REGISTRY:
            logger.warning("Overwriting existing prompt registration: %s", name)
        else:
            logger.debug("Registering new prompt: %s", name)
        cls._REGISTRY[name] = build_params

    @classmethod
    def get_prompt(cls, name: str, **kwargs) -> str:
        """
        Retrieve and build a prompt by name, optionally overriding or filling parameters.
        
        Args:
            name: The name of the registered prompt.
            **kwargs: Dynamic values to inject into the build process (e.g., 'schema', 'context').
        
        Returns:
            The fully constructed prompt string.
        
        Raises:
            KeyError: If the prompt name is not found.
        """
        if name not in cls._REGISTRY:
            logger.error("Prompt lookup failed: %s not found.", name)
            raise KeyError(f"Prompt '{name}' not found in registry. Available: {list(cls._REGISTRY.keys())}")

        # specific config for this prompt
        config = cls._REGISTRY[name].copy()

        # update with runtime arguments (e.g., injecting a specific schema or context)
        if kwargs:
            logger.debug(f"Building prompt {name} with overrides: {list(kwargs.keys())}")
        else:
            logger.debug(f"Building prompt {name} with default configuration.")

        # Update with runtime arguments (e.g., injecting a specific schema or context)
        config.update(kwargs)
        logger.info(f"config: {config}")

        return PromptLibrary.build(**config)

    @classmethod
    def list_prompts(cls) -> list[str]:
        """List all registered prompt names."""
        return list(cls._REGISTRY.keys())


# =============================================================================
# STANDARD PROMPT DEFINITIONS
# =============================================================================

# 1. General Assistant (Default Q Persona)
PromptRegistry.register("general_assistant", {
    "role": PromptPartials.DEFAULT_SYSTEM_ROLE,
    "instruction": "Assist the user with their request using available tools and knowledge.",
    "reasoning_pattern": PromptPartials.THOUGHT_PROCESS
})

# 2. Solicitation Section Extraction (Strict JSON)
PromptRegistry.register("solicitation_section_extraction", {
    "role": "You are an expert contract specialist.",
    "instruction": "Extract the standard Uniform Contract Format (UCF) sections from the provided solicitation document. For each identified section, provide its title, page range (if determinable), and a concise summary of its content. Strictly adhere to the JSON output format.",
    "reasoning_pattern": PromptPartials.SOLICITATION_SECTIONS,
    "output_format": "JSON"
    # 'schema' is expected to be passed at runtime via kwargs if not defined here
})

# 3. Solicitation Requirements Parsing (Compliance Focused)
PromptRegistry.register("solicitation_requirements_parsing", {
    "role": "You are a Senior Proposal Manager and Compliance Officer.",
    "instruction": "Ingest the provided solicitation document and map the requirements to the proposal structure.",
    "reasoning_pattern": f"{PromptPartials.SOLICITATION_SECTIONS}\n\n{PromptPartials.GOV_COMPLIANCE}",
    "output_format": "JSON"
})

# 4. Compliance Review (Red Team)
PromptRegistry.register("compliance_red_team", {
    "role": "You are a strict Government Compliance Officer.",
    "instruction": "Review the provided text for any non-compliance with the solicitation or FAR/DFARS regulations.",
    "reasoning_pattern": f"{PromptPartials.RED_TEAM_GOV}\n\n{PromptPartials.GOV_COMPLIANCE}",
    "output_format": "MARKDOWN"
})

# 5. Past Performance Evaluation
PromptRegistry.register("past_performance_eval", {
    "role": "You are a Source Selection Evaluation Board (SSEB) member.",
    "instruction": "Evaluate the provided project description against the solicitation's relevance and recency criteria.",
    "reasoning_pattern": f"{PromptPartials.PAST_PERFORMANCE}\n\n{PromptPartials.EVALUATION_SCORING}",
    "output_format": "MARKDOWN"
})

# 6. Vendor Risk Assessment (proposal-focused)
PromptRegistry.register("vendor_risk_assessment", {
    "role": "You are a capture risk analyst assessing a single vendor's proposal.",
    "instruction": "Review the vendor's response content and identify risks grounded in that proposal. Return only JSON.",
    "reasoning_pattern": f"{PromptPartials.THREAT_MODELING}\n\n{PromptPartials.CONTEXT_FIDELITY}",
    "output_format": "JSON",
    "additional_constraints": "Do NOT group risks under category headings. Emit each risk as a separate object in the risks array; include evidence quotes from the vendor response."
})
