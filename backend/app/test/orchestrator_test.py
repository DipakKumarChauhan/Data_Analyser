from app.core.orchestrator import orchestrator

from app.core.dataset_manager import dataset_manager
from app.core.session_manager import session_manager

import sys
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Initialize manually
dataset_manager.load_titanic_dataset()
session_manager.initialize_default_session(dataset_manager)

dm = session_manager.get_dataset_manager("titanic_default")
df = dm.get_dataframe()

# intent = {
#     "intent": "analytics",
#     "operation": "mean",
#     "columns": ["age"]
# }

intent = {
    "intent": "visualization",
    "chart_type": "histogram",
    "columns": ["age"]
}

response = orchestrator.execute("titanic_default", intent)

print(response)