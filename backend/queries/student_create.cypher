// Student graph: the student node + a copy of every topic with KNOWS (mastery starts at 0)
MERGE (s:Student {id: $student.id})
ON CREATE SET s.created_at = $now
SET s.name = $student.name, s.target_role = $student.target_role
WITH s
UNWIND $topics AS t
MERGE (tp:Topic {id: t.id})
SET tp.name = t.name, tp.area = t.area, tp.role_weight = t.weight, tp.foundational = t.foundational
MERGE (s)-[k:KNOWS]->(tp)
ON CREATE SET k.mastery = 0.0, k.attempts = 0
