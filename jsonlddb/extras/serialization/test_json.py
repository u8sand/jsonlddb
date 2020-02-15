import tempfile
from jsonlddb import JsonLDDatabase
from jsonlddb.extras import examples
from jsonlddb.extras.serialization import json

try:
  from jsondiff import diff
except ImportError:
  import logging
  logging.warning('install jsondiff for easier debugging')
  diff = lambda a, b: str((a, b))

def test_json():
  tmp = tempfile.mktemp()
  db = JsonLDDatabase().insert(examples.familial_ownership)
  json.dump(db, tmp)
  db_recover = json.load(tmp)
  assert db.index.spo == db_recover.index.spo, diff(db.index.spo, db_recover.index.spo)
  #
  json.dump(db, open(tmp, 'w'))
  db_recover = json.load(open(tmp, 'r'))
  assert db.index.spo == db_recover.index.spo, diff(db.index.spo, db_recover.index.spo)
