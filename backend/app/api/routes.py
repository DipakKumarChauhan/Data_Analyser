
from fastapi import APIRouter , UploadFile, File, HTTPException
from app.core.dataset_manager import dataset_manager
from app.core.session_manager import session_manager
import os
import pandas as pd
from io import StringIO

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