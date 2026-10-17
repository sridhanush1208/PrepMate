// Student profile
MATCH (s:Student)
RETURN s.id AS id, s.name AS name, s.target_role AS target_role, s.created_at AS created_at
