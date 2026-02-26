import uuid 
import pandas as pd
from typing import Dict, Any

from app.utils.preprocessing import preprocess_data
from app.core.dataset_manager import DatasetManager

class SessionManager:

    def __init__(self):
        self.sessions:Dict[str, DatasetManager] ={}

        self.default_session_id = 'titanic_default'

    def initialize_default_session(self, base_dataset_manager: DatasetManager):
        
        self.sessions[self.default_session_id] = base_dataset_manager

    def create_session_from_dataframe(self, df: pd.DataFrame) -> str:
        session_id = str(uuid.uuid4())
        dataset_manager = DatasetManager()
        dataset_manager.raw_df = df.copy()
        dataset_manager.analysis_df = preprocess_data(df.copy())
        dataset_manager.schema = dataset_manager._generate_schema(dataset_manager.analysis_df)

        self.sessions[session_id] = dataset_manager
        return session_id
    
    def get_dataset_manager(self, session_id:str) ->DatasetManager:
        if session_id not in self.sessions:
            raise ValueError(f"Session with ID '{session_id}' does not exist.")
        return self.sessions[session_id]
    
    def list_sessions(self):
        return list(self.sessions.keys())
    
session_manager = SessionManager()