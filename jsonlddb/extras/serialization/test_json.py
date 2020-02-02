import tempfile
from jsonlddb.extras import examples
from jsonlddb.extras.serialization import json

try:
  from jsondiff import diff
except ImportError:
  import logging
  logging.warn('install jsondiff for easier debugging')
  diff = lambda a, b: str((a, b))

def test_json():
  tmp = tempfile.mktemp()
  db = examples.familial_ownership
  json.dump(db, tmp)
  db_recover = json.load(tmp)
  assert db.index.spo == db_recover.index.spo, diff(db.index.spo, db_recover.index.spo)
