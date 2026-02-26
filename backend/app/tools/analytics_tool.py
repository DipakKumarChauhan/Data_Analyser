import pandas as pd

def calculate_mean(df:pd.DataFrame, column:str) -> float:
    """
        This Function Calculates the Mean of a Specific Column in a DataFrame
    """
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found in DataFrame.")
    if not pd.api.types.is_numeric_dtype(df[column]):
        raise ValueError(f"Column '{column}' is not numeric.")
    return float(df[column].mean())

def calculate_percentage(df:pd.DataFrame, column:str, value) -> float:
    """
        This Function Calculates the percentage of Rows that have Same Value in a Specific Column
    """
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found in DataFrame.")
    
    total = len(df)

    match_count =  (df[column] == value).sum()

    percentage = (match_count / total) * 100 if total > 0 else 0.0

    return float(round(percentage, 2))


def value_counts(df: pd.DataFrame, column: str):
    """
    This Function Calculates the Value Counts of a Specific Column in a DataFrame 
    """
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found in DataFrame.")

    return df[column].value_counts().to_dict() # .value_counts() returns the frequency count and to_dict() converts it to a dictionary format. 
