// Catalog: (a)-[:PREREQ_OF]->(b) means "learn a before b".
// DEPENDS_ON is the reverse edge, used only for PageRank.
UNWIND $prereqs AS p
MATCH (a:Topic {id: p.src}), (b:Topic {id: p.dst})
MERGE (a)-[:PREREQ_OF]->(b)
MERGE (b)-[:DEPENDS_ON]->(a)
