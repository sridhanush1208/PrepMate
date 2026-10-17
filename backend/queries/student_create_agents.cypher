// Student graph: one node per agent (they all share this graph)
UNWIND $agents AS name
MERGE (:Agent {name: name})
