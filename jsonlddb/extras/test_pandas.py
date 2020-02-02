from jsonlddb.extras import pandas, examples

try:
  from jsondiff import diff
except ImportError:
  import logging
  logging.warning('install jsondiff for easier debugging')
  diff = lambda a, b: str((a, b))

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
      object='Car',
    ),
  ])
  assert db.index.spo == db_recover.index.spo, diff(db.index.spo, db_recover.index.spo)
