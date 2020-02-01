from jsonlddb.extras import pandas, examples

def test_pandas():
  db = examples.familial_ownership
  dfs = pandas.to_dfs(db)
  db_recover = pandas.from_dfs(dfs, [
    dict(
      through='Person__childOf_Person',
      through_subject='Person',
      through_object='childOf_Person',
      subject='Person',
      predicate='childOf',
      object='Person',
    ),
    dict(
      subject='Person',
      predicate='spouseOf',
      object='Person',
    ),
    dict(
      subject='Person',
      predicate='owns',
      object='Person',
    ),
  ])
  assert db == db_recover
