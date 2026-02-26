import pandas as pd
import plotly.express as px

def create_histogram(df:pd.DataFrame, column:str):
    fig =  px.histogram(
        df,
        x= column,
        title=f'Distribution of {column}',
    )
    return fig

def create_bar_chart(df:pd.DataFrame, column:str):
    counts = df[column].value_counts().reset_index()
    counts.columns = [column, 'count']
    
    fig =  px.bar(
        counts,
        x=column,
        y='count',
        title=f'Value Counts of {column}',
    )
    return fig

def create_scatter(df:pd.DataFrame, x:str, y:str):
    fig = px.scatter(
        df,
        x=x,
        y=y,
        title=f'Scatter Plot of {y} vs {x}',
    )
    return fig

def create_3d_scatter(df:pd.DataFrame, x:str, y:str, z:str):
    fig = px.scatter_3d(
        df,
        x=x,
        y=y,
        z=z,
        title=f'3D Scatter Plot of {z} vs {x} and {y}',
    )
    return fig

def create_pie_chart(df: pd.DataFrame, column: str):
    counts = df[column].value_counts().reset_index()
    counts.columns = [column, "count"]

    # guardrail
    if len(counts) > 8:
        raise ValueError("Too many categories for pie chart")

    fig = px.pie(
        counts,
        names=column,
        values="count",
        title=f"Proportion of {column}"
    )
    return fig

def create_area_chart(df: pd.DataFrame, column: str):
    if not pd.api.types.is_numeric_dtype(df[column]):
        raise ValueError("Area chart requires numeric column")

    counts = (
        df[column]
        .dropna()
        .value_counts()
        .sort_index()
        .reset_index()
    )

    counts.columns = [column, "count"]

    fig = px.area(
        counts,
        x=column,
        y="count",
        title=f"Area Distribution of {column}"
    )
    return fig