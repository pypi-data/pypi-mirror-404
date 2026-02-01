import logging
import textwrap
from typing import Any, Optional

from jinja2 import Template

logger = logging.getLogger(__name__)
prompt_template = """
<system_role>
{{ role }}
</system_role>
{% if context %}
<context>
{{ context }}
</context>
{% endif %}
<instructions>
{{ instruction }}
</instructions>

<formatting_requirements>
{{ formatting_instruction }}
{% if examples %}
Refer to the following examples for schema structure:
<examples>
{{ examples }}
</examples>
{% endif -%}
</formatting_requirements>

<solicitation_document>
{{ data }}
</solicitation_document>
{% if final_instruction %}   
<final_instruction>
{{ final_instruction }}
</final_instruction>
{% endif -%}
"""


class PromptLibrary:
    """
    Central repository for building and retrieving composed prompts.
    """

    @staticmethod
    def _compile_template(template_str: str, **kwargs: Any) -> str:
        """Helper to render a Jinja2 template string."""
        template = Template(template_str)
        return template.render(**kwargs)

    @staticmethod
    def build(
            role: str,
            instruction: str,
            formatting_instruction: str,
            final_instruction: str,
            data: str,
            context: Optional[str] = None,
            examples: Optional[str] = None,
    ) -> str:
        """
        Advanced prompt builder supporting all patterns.
        
        Args:
            role: The system persona (default: Q).
            instruction: The core task instruction.
            formatting_instruction: The formatting requirements for the output.
            final_instruction: The final instruction for the task.
            data: The input data to be processed.
            context: Additional context for the task.
            examples: Few-shot examples string (injected into FEW_SHOT template).
        """
        clean_template: str = textwrap.dedent(prompt_template).strip()
        prompt: str = PromptLibrary._compile_template(clean_template,
            role=role,
            instruction=instruction,
            formatting_instruction=formatting_instruction,
            final_instruction=final_instruction,
            data=data,
            context=context,
            examples=examples
        )

        logger.info(f"Prompt built successfully. Total length: {len(prompt)} chars")
        if not context:
            context = ""
        if not examples:
            examples = ""
        if not final_instruction:
            final_instruction = ""
        logger.info(f"Prompt built:\nrole: {role}\ninstruction: {instruction}\nformatting_instruction: {formatting_instruction}\nfinal_instruction: {final_instruction}\ndata: {data[:100]}...\ncontext: {context[:100]}\nexamples: {examples}\n")
        return prompt


if __name__ == "__main__":
    role = "You are an expert senior Contracting Officer charged with analyzing solicitations and evaluating contract proposals."
    instruction = """You are tasked with extracting the "Evaluation Criteria" from the provided document.
    1. Look for Section M or "Evaluation Factors for Award".
    2. Identify distinct factors (e.g., "Technical Approach", "Past Performance").
    3. Extract the specific description and relative importance (if stated) for each.
    4. If no criteria are found, return the standard JSON object with an empty list in the "criteria" field."""
    formatting_instruction = """You must strictly output the result in JSON format.
The JSON object must include a "_reasoning" key first, where you explain where you found the data and your logic."""
    final_instruction = """    1. Analyze the text inside <solicitation_document> above.
    2. locate the data requested in <instructions>.
    3. First, formulate your reasoning in the "_reasoning" field.
    4. Then, populate the data fields strictly adhering to the <formatting_requirements>.
    5. Output ONLY the JSON object."""
    context = "This contract is similar to the BigData contract from the previous year."
    examples = """
    {
      "_reasoning": "Found evaluation factors in Section M.2. The document lists three distinct hierarchical factors.",
      "criteria": [
          {
              "name": "Technical Approach",
              "description": "The offeror must demonstrate...",
              "source_text_snippet": "Factor 1: Technical Approach..."
          }
      ]
    }    
    """
    data = "Title: NIOSH Information Technology Services (NITS)\nRFP number: 1331L521R13OS0006\nNAICS code: 336110\nPSC code: 1111\nContracting office: NIOSH"

    print(PromptLibrary.build(
        role=role,
        instruction=instruction,
        formatting_instruction=formatting_instruction,
        final_instruction=final_instruction,
        data=data,
        context=context,
        examples=examples
    ))
