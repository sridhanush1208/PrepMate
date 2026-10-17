// Student graph: copy prerequisite edges so multi-hop queries run inside one graph
UNWIND $prereqs AS p
MATCH (a:Topic {id: p.src}), (b:Topic {id: p.dst})
MERGE (a)-[:PREREQ_OF]->(b)
