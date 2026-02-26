import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Any

from app.config import settings
from app.utils.preprocessing import preprocess_data

class DatasetManager:

    def __init__(self):
        self.raw_df = None
        self.analysis_df = None
        self.schema = None
    
    def load_titanic_dataset(self):
        dataset_path =  Path(settings.DATA_DIR) / settings.TITANIC_DATASET
        df = pd.read_csv(dataset_path)
        self.raw_df = df.copy() 

        self.analysis_df = preprocess_data(df)
        self.schema = self._generate_schema(self.analysis_df)

    def _generate_schema(self, df: pd.DataFrame) -> Dict[str, Any]:
        
        schema = {
            "columns": [],
            "numeric_columns":[],
            "categorical_columns":[],
            "missing_values": {}
        }

        for col in df.columns:

            dtype =  str(df[col].dtype)

            schema['columns'].append({
                "name": col,
                "dtype": dtype
            })

            if pd.api.types.is_numeric_dtype(df[col]):
                schema['numeric_columns'].append(col)
            else:
                schema['categorical_columns'].append(col)
            
            schema['missing_values'][col] = int(df[col].isna().sum())
        
        return schema
    def get_dataframe(self):
        return self.analysis_df
    def get_schema(self):
        return self.schema
    
dataset_manager = DatasetManager()
        