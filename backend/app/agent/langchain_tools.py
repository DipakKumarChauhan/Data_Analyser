from langchain_core.tools import StructuredTool
from pydantic import BaseModel
from typing import Optional

from app.agent.intent_parser import parse_intent
from app.core.orchestrator import orchestrator
from app.core.session_manager import session_manager

import json



class DatasetQueryInput(BaseModel):
    query: str
    session_id: Optional[str] = "titanic_default"



def dataset_analysis_tool(query: str, session_id: str = "titanic_default"):
    """
    High-level dataset analysis capability.

    Steps:
    1. Fetch dataset schema
    2. Parse intent using LangChain LLM
    3. Execute via orchestrator
    4. Return structured result
    """

    # Get dataset
    dataset_manager = session_manager.get_dataset_manager(session_id)
    schema = dataset_manager.get_schema()

    # LLM → structured intent
    intent = parse_intent(query, schema)

    # Deterministic execution
    result = orchestrator.execute(session_id, intent)

    return json.dumps({
        "text_response": result["text_response"],
        "chart": result["chart"],
        "data": result["data"]
    }, default=str)



dataset_analyst_tool = StructuredTool.from_function(
    name="dataset_analyst",
    description=(
        "ONLY tool for dataset analysis. Use this for ALL data questions including: "
        "statistics (mean, count, percentage), visualizations (histogram, bar chart, pie chart, scatter, area chart, 3d scatter), "
        "and aggregations (grouping, counting by categories). "
        "This tool handles everything - do not try to use other tools."
    ),
    func=dataset_analysis_tool,
    args_schema=DatasetQueryInput,
)



LANGCHAIN_TOOLS = [
    dataset_analyst_tool
]