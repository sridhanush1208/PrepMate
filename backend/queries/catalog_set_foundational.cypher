// Store the PageRank score on each topic
UNWIND $scores AS s
MATCH (t:Topic {id: s.topic_id})
SET t.foundational = s.score
