// Catalog: all topics with this role's focus weight (0 if not a focus)
MATCH (t:Topic)
OPTIONAL MATCH (:Role {id: $role})-[f:FOCUSES_ON]->(t)
RETURN t.id AS id, t.name AS name, t.area AS area,
       coalesce(f.weight, 0) AS weight, coalesce(t.foundational, 0.0) AS foundational
