// Catalog: role tracks and how much they focus on each topic
UNWIND $focus AS f
MERGE (r:Role {id: f.role_id})
SET r.name = f.role_name
WITH r, f
MATCH (t:Topic {id: f.topic})
MERGE (r)-[x:FOCUSES_ON]->(t)
SET x.weight = f.weight
