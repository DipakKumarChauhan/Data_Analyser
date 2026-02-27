
from fastapi import APIRouter , UploadFile, File, HTTPException
from pydantic import BaseModel

from app.agent.agent_executor import run_agent
from app.core.dataset_manager import dataset_manager
from app.core.session_manager import session_manager
import os
import pandas as pd
from io import StringIO

class ChatRequest(BaseModel):
    query: str
    # Session identifier for selecting which uploaded dataset to use.
    # Defaults to the Titanic dataset.
    session_id: str = "titanic_default"

router = APIRouter()


@router.get('/health')
def health_check():
    return {"status": "ok"}

@router.get('/dataset-schema')
def dataset_schema():
    schema = dataset_manager.get_schema()
    return schema

@router.post("/upload-dataset")
async def uplod_dataset(file:UploadFile = File(...)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed.")

    try:
        contents = await file.read()

        decoded =  contents.decode('utf-8')
        df = pd.read_csv(StringIO(decoded))

        if df.shape[0] == 0:
            raise HTTPException(status_code=400, detail="Uploaded CSV file is empty.")
        
        session_id =  session_manager.create_session_from_dataframe(df)
        dataset_manager = session_manager.get_dataset_manager(session_id)

        return {
            "session_id": session_id,
            "schema": dataset_manager.get_schema()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
    

@router.get('/dataset-schema/{session_id}')
def dataset_schema_by_session(session_id:str):
    schema =  session_manager.get_dataset_manager(session_id).get_schema()
    return schema

@router.post("/chat")
async def chat_endpoint(request: ChatRequest):

    try:
        # Pass session_id through so tools operate on the correct dataset
        result = run_agent(request.query, request.session_id)
        
        # Extract LLM response text
        response_text = result["response"].content if hasattr(result["response"], 'content') else str(result["response"])
        
        #response_text = result["response"]
        
        # Parse tool result data (chart and data)
        tool_result = result.get("tool_result")
        chart = None
        data = None
        
        if tool_result:
            import json
            try:
                # If tool_result is already a dict, use it directly
                if isinstance(tool_result, dict):
                    tool_data = tool_result
                else:
                    # If it's a string, parse it as JSON
                    tool_data = json.loads(tool_result)
                
                chart = tool_data.get("chart")
                data = tool_data.get("data")
            except Exception as e:
                pass

        return {
            "success": True,
            "response": response_text,
            "chart": chart,
            "data": data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))