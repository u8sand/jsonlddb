import tempfile
from jsonlddb.extras import examples
from jsonlddb.extras.serialization import msgpack

try:
  from jsondiff import diff
except ImportError:
  import logging
  logging.warning('install jsondiff for easier debugging')
  diff = lambda a, b: str((a, b))

def test_msgpack():
  tmp = tempfile.mktemp()
  db = examples.familial_ownership
  msgpack.dump(db, tmp)
  db_recover = msgpack.load(tmp)
  assert db.index.spo == db_recover.index.spo, diff(db.index.spo, db_recover.index.spo)
  #
  msgpack.dump(db, open(tmp, 'wb'))
  db_recover = msgpack.load(open(tmp, 'rb'))
  assert db.index.spo == db_recover.index.spo, diff(db.index.spo, db_recover.index.spo)
