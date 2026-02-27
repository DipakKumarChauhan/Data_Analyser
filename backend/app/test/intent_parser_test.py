from app.agent.intent_parser import parse_intent

intent = parse_intent(
    "What percentage of passengers were male?"
)

print(intent)