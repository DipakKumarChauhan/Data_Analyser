import pandas as pd 

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize the column names of a DataFrame by converting them to lowercase and replacing spaces with underscores.

    Args:
        df (pd.DataFrame): The input DataFrame with original column names.

    Returns:
        pd.DataFrame: A new DataFrame with normalized column names.
    """
    df.columns =(
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(' ', '_')
    )

    return df

def standardize_missing_values(df:pd.DataFrame) -> pd.DataFrame:
    """
    Standardize missing values in a DataFrame by replacing common placeholders with NaN.

    Args:
        df (pd.DataFrame): The input DataFrame with potential missing value placeholders.

    Returns:
        pd.DataFrame: A new DataFrame with standardized missing values.
    """
    
    df = df.replace(r'^\s*$', pd.NA, regex=True)  # Replace empty strings with NaN
    return df.replace(['NA', 'N/A', 'null', 'NULL', ''], pd.NA)

def enforce_types (df:pd.DataFrame) -> pd.DataFrame:
    """
    Enforce specific data types for columns in a DataFrame.

    Args:
        df (pd.DataFrame): The input DataFrame with original data types.

    Returns:
        pd.DataFrame: A new DataFrame with enforced data types.
    """
    for col in df.columns:
        if df[col].dtype == 'object':
            try:
                df[col] = pd.to_numeric(df[col])
            except Exception:
                pass  # If conversion fails, leave the column as is
    return df

def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:

    df =  normalize_columns(df)
    df =  standardize_missing_values(df)
    df = enforce_types(df)

    return df
