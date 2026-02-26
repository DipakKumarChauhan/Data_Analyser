import sys
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.core.dataset_manager import dataset_manager
from app.core.session_manager import session_manager

# Initialize manually
dataset_manager.load_titanic_dataset()
session_manager.initialize_default_session(dataset_manager)

# Now this works:
dm = session_manager.get_dataset_manager("titanic_default")
df = dm.get_dataframe()
from app.tools.analytics_tool import calculate_mean
print(calculate_mean(df, "age"))
from app.tools.visualization_tool import create_histogram
fig = create_histogram(df, "age")
fig.show()