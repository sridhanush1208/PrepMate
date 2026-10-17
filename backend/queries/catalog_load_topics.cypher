// Catalog: create topics
UNWIND $topics AS t
MERGE (tp:Topic {id: t.id})
SET tp.name = t.name, tp.area = t.area
