// Catalog: list topics (for matching topic names in chat)
MATCH (t:Topic)
RETURN t.id AS id, t.name AS name, t.area AS area
