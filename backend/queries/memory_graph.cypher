// Memory panel: every relationship except the message chain (filtered further in Python)
MATCH (a)-[r]->(b)
WHERE NOT a:Message AND NOT b:Message
RETURN a, r, b
