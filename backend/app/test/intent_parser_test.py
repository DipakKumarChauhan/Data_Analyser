from app.agent.intent_parser import parse_intent
from app.core.dataset_manager import dataset_manager
from app.core.session_manager import session_manager


dataset_manager.load_titanic_dataset()
session_manager.initialize_default_session(dataset_manager)

dm =  session_manager.get_dataset_manager("titanic_default")
df = dm.get_dataframe()
schema  =  dm.get_schema()

intent = parse_intent(
    "What percentage of passengers were male?",
    schema
)

print(intent)