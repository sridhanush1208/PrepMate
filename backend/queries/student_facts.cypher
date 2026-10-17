// Semantic recall: facts about the student
MATCH (f:Fact)
OPTIONAL MATCH (f)-[:ABOUT]->(x)
RETURN f.id AS id, f.text AS text, x.name AS about
ORDER BY f.updated DESC
LIMIT 15
