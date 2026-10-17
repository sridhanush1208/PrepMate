// Catalog: questions linked to the topic they test
UNWIND $questions AS q
MATCH (t:Topic {id: q.topic})
MERGE (qu:Question {id: q.id})
SET qu.text = q.text, qu.hint = q.hint, qu.points = q.points, qu.difficulty = q.difficulty
MERGE (qu)-[:TESTS]->(t)
