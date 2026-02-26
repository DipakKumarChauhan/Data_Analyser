import pandas as pd

def groupby_count(df:pd.DataFrame, column:str):
    """
        This Function Groups the DataFrame by a Specific Column and Counts the Number of Rows in Each Group
    """
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found in DataFrame.")
    result =  df.groupby(column).size().reset_index(name='count')
    return result

def groupby_mean(df: pd.DataFrame, group_col: str, value_col: str):
    if group_col not in df.columns or value_col not in df.columns:
        raise ValueError("Invalid column name")

    result = (
        df.groupby(group_col)[value_col]
        .mean()
        .reset_index(name="mean")
    )

    return result   
