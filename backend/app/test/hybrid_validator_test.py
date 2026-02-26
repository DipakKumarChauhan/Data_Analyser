import sys
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.core.dataset_manager import dataset_manager
from app.core.session_manager import session_manager
from app.core.tool_validator import validator

# Initialize manually
dataset_manager.load_titanic_dataset()
session_manager.initialize_default_session(dataset_manager)

dm = session_manager.get_dataset_manager("titanic_default")
df = dm.get_dataframe()

intent = {
    "intent": "visualization",
    "chart_type": "pie_chart",
    "columns": ["age"]
}

result = validator.validate_chart(df, intent)

print(result.corrected_intent)
print(result.message)