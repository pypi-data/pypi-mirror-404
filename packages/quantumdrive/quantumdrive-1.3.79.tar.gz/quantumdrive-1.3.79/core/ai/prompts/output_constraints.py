OUTPUT_CONSTRAINTS = """
### OUTPUT CONSTRAINTS

You must strictly adhere to the following output format:

**Format:** {{ format_type }}

{% if format_type == 'JSON' %}
**Specific JSON Schema:**
{{ schema }}
Do NOT include markdown formatting (like ```json ... ```) or any text before/after the JSON.
{% elif format_type == 'MARKDOWN' %}
Ensure the output is well-structured Markdown with appropriate headers, lists, and tables.
{% elif format_type == 'SQL' %}
Return ONLY valid SQL code. Do not wrap in markdown blocks if requested to output raw text.
{% endif %}

{{ additional_constraints }}
"""