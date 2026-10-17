// Practising a topic closes its open tasks
MATCH (tk:Task {status: 'todo'})-[:PRACTICES]->(:Topic {id: $topic_id})
SET tk.status = 'done', tk.done_at = $now, tk.key = tk.key + ':done:' + tk.id
RETURN count(tk) AS closed
