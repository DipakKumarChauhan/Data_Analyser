import json
from app.agent.llm_client import call_llm

INTENT_PROMPT = """
You convert user questions into structured JSON for a data analysis system.

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

Rules:
- Output ONLY valid JSON.
- Do NOT explain anything.
- Use lowercase column names.
- Choose best matching intent.

JSON FORMAT:

{
  "intent": "",
  "operation": "",
  "chart_type": "",
  "columns": [],
  "group_by": "",
  "value": ""
}

User Question:
"""

def parse_intent(user_query:str):
    
    prompt = INTENT_PROMPT + user_query

    raw_response = call_llm(prompt)

    try:
        intent = json.loads(raw_response)
        return intent
    except Exception:
        raise ValueError("LLM returned invalid JSON")