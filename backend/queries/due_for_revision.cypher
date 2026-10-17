// Forgetting curve: effective = mastery * 0.5 ^ (days since practice / half-life).
// Topics that were known but are now fading.
MATCH (:Student)-[k:KNOWS]->(t:Topic)
WHERE k.attempts > 0 AND k.mastery >= $weak
WITH t, k, k.mastery * (0.5 ^ (toFloat($now - k.last_practiced) / 86400000.0 / $half_life)) AS effective
WHERE effective < $weak
RETURN t.id AS topic_id, t.name AS topic, k.mastery AS mastery, effective
ORDER BY effective
LIMIT 5
