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
            return self._handle_analytics(df, intent)

        elif intent_type == "aggregation":
            return self._handle_aggregation(df, intent)

        elif intent_type == "visualization":
            return self._handle_visualization(df, intent)

        else:
            raise ValueError("Unsupported intent")

    
    # ANALYTICS
    
    def _handle_analytics(self, df, intent):

        validation = validator.validate_analytics(df, intent)
        intent = validation.corrected_intent

        column = intent["columns"][0]
        operation = intent.get("operation")

        if operation == "mean":
            result = calculate_mean(df, column)
            text = f"The average {column} is {result:.2f}"

        elif operation == "percentage":
            value = intent.get("value")
            result = calculate_percentage(df, column, value)
            text = f"{result}% of passengers have {column} = {value}"

        elif operation == "count":
            result = value_counts(df, column)
            text = f"Value counts for {column} calculated."

        else:
            raise ValueError("Unsupported analytics operation")

        return {
            "text_response": text,
            "chart": None,
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