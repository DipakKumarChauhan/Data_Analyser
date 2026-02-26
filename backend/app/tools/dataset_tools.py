import pandas as pd 
from typing import Dict , Any

def dateset_summary(df:pd.DataFrame) -> Dict[str, Any]:
    summary = {
        "num_rows":int(df.shape[0]),
        "num_columns": int(df.shape[1]),
        "columns": list(df.columns),
        "numeric_columns": df.select_dtypes(include='number').columns.tolist(),
        "categorical_columns": df.select_dtypes(exclude = 'number').columns.tolist(),
        "missing_values": df.isna().sum().to_dict(),
    }
    return summary