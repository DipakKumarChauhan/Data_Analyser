import json
from langchain_core.prompts import ChatPromptTemplate
from app.agent.llm_client import llm


PROMPT = ChatPromptTemplate.from_template("""
STRICT: Return ONLY valid JSON. NO explanations. NO text.                                          
You convert user questions into structured JSON for data analysis.

AVAILABLE DATASET COLUMNS:
{columns}

IMPORTANT RULES:
- You MUST ONLY use column names from the provided list.
- Never invent column names.
- Output ONLY JSON.

Allowed intents:
- analytics
- aggregation
- visualization

Allowed analytics operations:
- mean
- percentage
- count

Allowed charts:
- histogram
- bar_chart
- pie_chart
- area_chart
- scatter
- 3d_scatter

Guidelines for visualization questions:
- If the user explicitly mentions a chart type (histogram, bar chart, pie chart, area chart, scatter, 3d scatter),
  you MUST set:
  - "intent": "visualization"
  - "chart_type": "<that_chart_type>"
  - "columns": ["<main_column_to_plot>"]
- Examples:
  - "Show survival distribution as pie chart" →
    - "intent": "visualization", "chart_type": "pie_chart", "columns": ["survived"]
  - "Show age distribution as area chart" →
    - "intent": "visualization", "chart_type": "area_chart", "columns": ["age"]
- Do NOT use "analytics" + "operation": "mean" for questions that clearly ask to visualize or plot a distribution.

Guidelines for percentage questions:
- When the user asks "What percentage of people/rows have X?", use:
  - "operation": "percentage"
  - "columns": ["<COLUMN_NAME_FOR_X>"]
  - "value": "<EXACT_VALUE_OF_X_IN_THAT_COLUMN>"
- Examples:
  - "What percentage of people survived?" →
    - "columns": ["survived"], "value": "1" (or the positive class for survival)
  - "What percentage of passengers were male?" →
    - "columns": ["sex"], "value": "male"
- When the user asks about missing or NaN values (e.g. "what percentage of values are missing/NaN/null"),
  always set:
  - "operation": "percentage"
  - "columns": ["<COLUMN_NAME>"]
  - "value": "missing"
- Never put a column name (like "survived") into the "value" field.
- Never leave "value" empty for percentage questions unless the condition is truly unspecified.

Guidelines for missing-value count questions:
- When the user asks "How many missing values are there in COLUMN?" or similar:
  - Use "intent": "analytics"
  - Use "operation": "count"
  - Use "columns": ["<COLUMN_NAME>"]
  - Use "value": "missing"
- When the user asks "How many non-missing / not null values are there in COLUMN?":
  - Use "intent": "analytics"
  - Use "operation": "count"
  - Use "columns": ["<COLUMN_NAME>"]
  - Use "value": "non-missing"

JSON FORMAT:
{{
  "intent": "",
  "operation": "",
  "chart_type": "",
  "columns": [],
  "group_by": "",
  "value": ""
}}

User Question:
{question}
""")

def build_schema_text(schema:dict):
    cols = [c["name"] for c in schema['columns']]
    return ", ".join(cols)

def parse_intent(question: str,schema: dict):
    
    schema_text = build_schema_text(schema)

    chain = PROMPT | llm

    response = chain.invoke({"question": question, "columns": schema_text})
    content = response.content.strip()

    # Debug: Print the raw response
    print(f"DEBUG - Raw LLM Response:\n{content}\n")

    # Handle common LLM response formats - SAFE VERSION
    if content.startswith("```json"):
        # Extract JSON from markdown code block
        parts = content.split("```json")
        if len(parts) > 1:
            content = parts[1].split("```")[0].strip()
    elif content.startswith("```"):
        # Extract from generic code block
        parts = content.split("```")
        if len(parts) > 1:
            content = parts[1].strip()
            if "```" in content:
                content = content.split("```")[0].strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        print(f"ERROR - Failed to parse JSON: {e}")
        print(f"ERROR - Content was: {content}")
        raise ValueError(f"Invalid JSON returned by LLM: {str(e)}")