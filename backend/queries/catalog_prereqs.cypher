// Catalog: every prerequisite edge
MATCH (a:Topic)-[:PREREQ_OF]->(b:Topic)
RETURN a.id AS src, b.id AS dst
