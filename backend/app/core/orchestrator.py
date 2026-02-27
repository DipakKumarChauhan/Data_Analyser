from typing import Dict, Any

from app.core.session_manager import session_manager
from app.core.tool_validator import validator

# tools
from app.tools.analytics_tool import (
    calculate_mean,
    calculate_percentage,
    value_counts,
)

from app.tools.aggregation_tool import (
    groupby_count,
    groupby_mean,
)

from app.tools.visualization_tool import (
    create_histogram,
    create_bar_chart,
    create_pie_chart,
    create_area_chart,
    create_scatter,
    create_3d_scatter,
)


class QueryOrchestrator:

    
    # MAIN ENTRY
    
    def execute(self, session_id: str, intent: Dict[str, Any]):

        dataset_manager = session_manager.get_dataset_manager(session_id)
        df = dataset_manager.get_dataframe()

        intent_type = intent.get("intent")

        if intent_type == "analytics":
            # Pass both the DataFrame and its schema so analytics logic can
            # reuse precomputed metadata (like missing value counts).
            schema = dataset_manager.get_schema()
            return self._handle_analytics(df, schema, intent)

        elif intent_type == "aggregation":
            return self._handle_aggregation(df, intent)

        elif intent_type == "visualization":
            return self._handle_visualization(df, intent)

        else:
            raise ValueError("Unsupported intent")

    
    # ANALYTICS
    
    def _handle_analytics(self, df, schema, intent):

        validation = validator.validate_analytics(df, intent)
        intent = validation.corrected_intent

        column = intent["columns"][0]
        operation = intent.get("operation")

        if operation == "mean":
            result = calculate_mean(df, column)
            text = f"The average {column} is {result:.2f}"

        elif operation == "percentage":
            value = intent.get("value")

            # Normalize value for special percentage queries like:
            # - "not 0"          → values != 0
            # - "non-missing"    → values that are not NaN
            # - "nan"/"missing"  → values that are NaN
            normalized = (
                str(value).strip().lower()
                if value is not None
                else ""
            )

            # Prefer precomputed missing-value stats from the schema when available
            missing_values_map = (schema or {}).get("missing_values", {})
            missing_count_from_schema = missing_values_map.get(column)
            total_rows = len(df[column])

            # 1) Special handling for inequality / missingness style questions
            if normalized in {"not 0", "nonzero", "!=0", "not_zero"}:
                total = total_rows
                if total == 0:
                    result = 0.0
                else:
                    mask = df[column] != 0
                    pct = (mask.sum() / total) * 100
                    result = float(round(pct, 2))
                text = f"{result}% of values in {column} are not 0."

            elif normalized in {
                "non-missing",
                "not missing",
                "non missing",
                "not null",
                "non-null",
                "non null",
                "not nan",
                "non-nan",
                "non nan",
            }:
                # Percentage of non-missing values, prefer schema counts
                total = total_rows
                if total == 0:
                    result = 0.0
                else:
                    if missing_count_from_schema is not None:
                        non_missing = total - missing_count_from_schema
                    else:
                        non_missing = df[column].notna().sum()
                    pct = (non_missing / total) * 100
                    result = float(round(pct, 2))
                text = f"{result}% of values in {column} are non-missing."

            elif normalized in {"nan", "missing", "null"}:
                # Percentage of missing/NaN values, prefer schema counts
                total = total_rows
                if total == 0:
                    result = 0.0
                else:
                    if missing_count_from_schema is not None:
                        missing = missing_count_from_schema
                    else:
                        missing = df[column].isna().sum()
                    pct = (missing / total) * 100
                    result = float(round(pct, 2))
                text = f"{result}% of values in {column} are NaN or missing."

            # 2) Default: equality percentage (possibly inferring a sensible default value)
            else:
                # If the LLM didn't specify a value explicitly, try to infer a sensible default.
                # This is important for questions like "What percentage of people survived?"
                # where the user clearly refers to the "positive" class of a binary column.
                if value in (None, "", " "):
                    non_null = df[column].dropna()
                    unique_vals = non_null.unique()

                    inferred_value = None

                    # Binary / boolean-like columns: choose the "positive" class
                    if len(unique_vals) == 2:
                        try:
                            # If values are numeric-like (e.g. 0/1), pick the larger one
                            numeric_vals = sorted(unique_vals)
                            inferred_value = numeric_vals[-1]
                        except Exception:
                            # Fallback: pick the most frequent non-null value
                            inferred_value = non_null.mode(dropna=True).iloc[0]
                    else:
                        # General case: use the most frequent non-null value
                        inferred_value = non_null.mode(dropna=True).iloc[0]

                    value = inferred_value
                    intent["value"] = value

                result = calculate_percentage(df, column, value)
                text = f"{result}% of passengers have {column} = {value}"

        elif operation == "count":
            value = intent.get("value")
            normalized = (
                str(value).strip().lower()
                if value is not None
                else ""
            )

            # Prefer precomputed missing-value stats from the schema when available
            missing_values_map = (schema or {}).get("missing_values", {})
            missing_count_from_schema = missing_values_map.get(column)
            total_rows = len(df[column])

            # Special handling for missing / non-missing count questions
            if normalized in {"nan", "missing", "null"}:
                if missing_count_from_schema is not None:
                    result = int(missing_count_from_schema)
                else:
                    result = int(df[column].isna().sum())
                text = f"There are {result} missing values in {column}."
                chart_json = None

            elif normalized in {
                "non-missing",
                "not missing",
                "non missing",
                "not null",
                "non-null",
                "non null",
                "not nan",
                "non-nan",
                "non nan",
            }:
                if missing_count_from_schema is not None and total_rows is not None:
                    result = int(total_rows - missing_count_from_schema)
                else:
                    result = int(df[column].notna().sum())
                text = f"There are {result} non-missing values in {column}."
                chart_json = None

            else:
                # Default: value counts distribution
                result = value_counts(df, column)
                text = f"Value counts for {column} calculated."

                # Additionally generate a bar chart for count distributions,
                # so queries like "number of passengers by class" produce a chart.
                try:
                    fig = create_bar_chart(df, column)
                    chart_json = fig.to_json()
                except Exception:
                    chart_json = None

        else:
            raise ValueError("Unsupported analytics operation")

        return {
            "text_response": text,
            "chart": chart_json if operation == "count" else None,
            "data": result,
        }

    # AGGREGATION
    
    def _handle_aggregation(self, df, intent):

        group_col = intent.get("group_by")
        value_col = intent["columns"][0]
        operation = intent.get("operation")

        group_col = validator.validate_column(df, group_col)
        value_col = validator.validate_column(df, value_col)

        if operation == "mean":
            result_df = groupby_mean(df, group_col, value_col)
            text = f"Average {value_col} grouped by {group_col}"

        elif operation == "count":
            result_df = groupby_count(df, group_col)
            text = f"Counts grouped by {group_col}"

        else:
            raise ValueError("Unsupported aggregation")

        return {
            "text_response": text,
            "chart": None,
            "data": result_df.to_dict(orient="records"),
        }

   
    # VISUALIZATION
    
    def _handle_visualization(self, df, intent):

        validation = validator.validate_chart(df, intent)
        intent = validation.corrected_intent

        chart_type = intent["chart_type"]
        cols = intent["columns"]

        if chart_type == "histogram":
            fig = create_histogram(df, cols[0])

        elif chart_type == "bar_chart":
            fig = create_bar_chart(df, cols[0])

        elif chart_type == "pie_chart":
            fig = create_pie_chart(df, cols[0])

        elif chart_type == "area_chart":
            fig = create_area_chart(df, cols[0])

        elif chart_type == "scatter":
            fig = create_scatter(df, cols[0], cols[1])

        elif chart_type == "3d_scatter":
            fig = create_3d_scatter(df, cols[0], cols[1], cols[2])

        else:
            raise ValueError("Unsupported chart")

        return {
            "text_response": f"Generated {chart_type} visualization.",
            "chart": fig.to_json(),
            "data": None,
        }


orchestrator = QueryOrchestrator()