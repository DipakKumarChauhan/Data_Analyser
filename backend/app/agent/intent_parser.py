# import json
# from langchain_core.prompts import ChatPromptTemplate
# from app.agent.llm_client import call_llm

# INTENT_PROMPT = """
# You convert user questions into structured JSON for a data analysis system.

# Allowed intents:
# - analytics
# - aggregation
# - visualization

# Allowed analytics operations:
# - mean
# - percentage
# - count

# Allowed charts:
# - histogram
# - bar_chart
# - pie_chart
# - area_chart
# - scatter
# - 3d_scatter

# Rules:
# - Output ONLY valid JSON.
# - Do NOT explain anything.
# - Use lowercase column names.
# - Choose best matching intent.

# JSON FORMAT:

# {
#   "intent": "",
#   "operation": "",
#   "chart_type": "",
#   "columns": [],
#   "group_by": "",
#   "value": ""
# }

# User Question:
# """

# def parse_intent(user_query:str):
    
#     prompt = INTENT_PROMPT + user_query

#     raw_response = call_llm(prompt)

#     try:
#         intent = json.loads(raw_response)
#         return intent
#     except Exception:
#         raise ValueError("LLM returned invalid JSON")

import json
from langchain_core.prompts import ChatPromptTemplate
from app.agent.llm_client import llm


PROMPT = ChatPromptTemplate.from_template("""
You convert user questions into structured JSON for data analysis.

AVAILABLE DATASET COLUMNS:
{columns}

IMPORTANT RULES:
- You MUST ONLY use column names from the provided list.
- Never invent column names.
- Output ONLY JSON.

Allowed intents:
analytics, aggregation, visualization

Allowed analytics operations:
mean, percentage, count

Allowed charts:
histogram, bar_chart, pie_chart, area_chart, scatter, 3d_scatter

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

    # Handle common LLM response formats
    if content.startswith("```json"):
        # Extract JSON from markdown code block
        content = content.split("```json")[1].split("```")[0].strip()
    elif content.startswith("```"):
        # Extract from generic code block
        content = content.split("```")[1].split("```")[0].strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        print(f"ERROR - Failed to parse JSON: {e}")
        print(f"ERROR - Content was: {content}")
        raise ValueError(f"Invalid JSON returned by LLM: {str(e)}")