from typing import Dict , Any
import pandas as pd
from rapidfuzz import process
import difflib

COLUMN_ALIASES = {
    "gender": "sex",
    "gender_type": "sex",
    "ticket_price": "fare",
    "price": "fare",
    "passenger_class": "pclass"
}

class ValidationResult:
    def __init__(self, valid:bool, corrected_intent: Dict[str,Any],message:str = ""):
        self.valid = valid
        self.corrected_intent = corrected_intent
        self.message = message

class HybridValidator:
    # Column Validations

    def validate_column(self, df:pd.DataFrame, column:str)-> str:        
        column = column.lower().strip()

        
        if column in df.columns:
            return column
        
        if column in COLUMN_ALIASES:
            alias = COLUMN_ALIASES[column]
            if alias in df.columns:
                return alias

            # Fuzzy fallback performs partial substring matching to recover from non-exact column names and improves usability by allowing approximate column inputs.
        # for col in df.columns:
        #     if column in col :
        #         return col
            # Basic Fallback logic only checks fr substrin match

        # Difflib fallback uses sequence matching to find the closest column name, providing a more robust recovery mechanism for misspelled or approximate column inputs.

        # columns = [c.lower() for c in df.columns]

        # # 1️⃣ Exact match
        # if column in columns:
        #     return df.columns[columns.index(column)]

        # # 2️⃣ Fuzzy similarity match
        # match = difflib.get_close_matches(column, columns, n=1, cutoff=0.6)

        # if match:
        #     return df.columns[columns.index(match[0])]

        # rapidfuzz fallback uses a more efficient algorithm for fuzzy string matching, providing faster and more accurate results when recovering from non-exact column names.
        # Fastest Option for large datasets with many columns, as it is optimized for performance while still providing robust fuzzy matching capabilities.
        match, score, _ = process.extractOne(column, df.columns)

        if score > 70:
            return match

        raise ValueError(f"Column '{column}' not found in DataFrame.")
    

    #### Type Helper ##########
    def is_numeric(self, df, column):
        return pd.api.types.is_numeric_dtype(df[column])

    def is_categorical(self, df, column):
        return not self.is_numeric(df, column)


    ##########################
    # Chart Type Validation
    ############################

    def validate_chart(self, df, intent: Dict[str,Any]) -> ValidationResult:
        
        chart =  intent.get("chart_type")
        columns = intent.get("columns", [])

        if not columns: 
            return ValidationResult(False, intent, "No columns specified for chart.")
        
        column =  self.validate_column(df, columns[0])

        if chart == "histogram":
            if not self.is_numeric(df, column):
                intent['chart_type'] = "bar_chart"
                return ValidationResult(True, intent, "Histogram invalid switched to bar chart")
        
        # PIE CHART
        if chart == "pie_chart":
            if self.is_numeric(df, column):
                intent["chart_type"] = "histogram"
                return ValidationResult(True, intent,
                                        "Pie invalid for numeric → histogram used")

            if df[column].nunique() > 8:
                intent["chart_type"] = "bar_chart"
                return ValidationResult(True, intent,
                                        "Too many categories → bar chart used")

        # AREA CHART
        if chart == "area_chart":
            if not self.is_numeric(df, column):
                intent["chart_type"] = "bar_chart"
                return ValidationResult(True, intent,
                                        "Area requires numeric → bar chart used")

        return ValidationResult(True, intent)
    
    def validate_analytics(self, df, intent):

        column = self.validate_column(df, intent["columns"][0])
        intent["columns"][0] = column

        operation = intent.get("operation")

        if operation == "mean":
            if not self.is_numeric(df, column):
                raise ValueError("Mean requires numeric column")

        return ValidationResult(True, intent)

validator = HybridValidator()



