// Catalog: list role tracks
MATCH (r:Role)
RETURN r.id AS id, r.name AS name
ORDER BY r.name
