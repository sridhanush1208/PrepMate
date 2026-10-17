// Coordination: the Planner puts a task on the shared board for another agent.
// key = "<agent>:<topic>" while open, so the same task is not added twice.
MATCH (ag:Agent {name: $assign_to}), (p:Agent {name: $agent}), (tp:Topic {id: $topic_id})
MERGE (tk:Task {key: $key})
ON CREATE SET tk.id = $id, tk.title = $title, tk.due = $due, tk.status = 'todo', tk.ts = $now
MERGE (tk)-[:ASSIGNED_TO]->(ag)
MERGE (tk)-[:PRACTICES]->(tp)
MERGE (p)-[:WROTE]->(tk)
RETURN tk.id AS id
