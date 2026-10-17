// Questions this student already answered (so we don't repeat them)
MATCH (:Attempt)-[:ON]->(q:Question)
RETURN collect(DISTINCT q.id) AS ids
