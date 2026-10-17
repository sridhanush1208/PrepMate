// Graph algorithm: PageRank over DEPENDS_ON edges.
// A topic that many other topics depend on gets a high "foundational" score.
CALL algo.pageRank('Topic', 'DEPENDS_ON')
YIELD node, score
RETURN node.id AS topic_id, score
