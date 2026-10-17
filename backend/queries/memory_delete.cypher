// "Forget this": delete one fact or rule (its relationships go with it)
MATCH (x {id: $id})
WHERE x:Fact OR x:Rule
DELETE x
