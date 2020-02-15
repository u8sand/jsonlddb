import os
import tempfile
import shutil
from datapackage import DataPackage
from jsonlddb import JsonLDDatabase
from jsonlddb.extras import examples, datapackage, generate

try:
  from jsondiff import diff
except ImportError:
  import logging
  logging.warning('install jsondiff for easier debugging')
  diff = lambda a, b: str((a, b))

def test_datapackage_example():
  db = JsonLDDatabase().insert(examples.familial_ownership)
  tmpdir = tempfile.mkdtemp()
  datapackage.to_datapackage(db, tmpdir)
  pkg = DataPackage(os.path.join(tmpdir, 'datapackage.json'))
  errors = pkg.errors
  db_recover = datapackage.from_datapackage(tmpdir)
  shutil.rmtree(tmpdir)
  assert errors == [], errors
  assert db.index.spo == db_recover.index.spo, diff(db.index.spo, db_recover.index.spo)

def test_datapackage_random():
  db = JsonLDDatabase().insert(list(generate.random_jsonld(100, 5, 2, 5, 2, 5)))
  tmpdir = tempfile.mkdtemp()
  datapackage.to_datapackage(db, tmpdir)
  pkg = DataPackage(os.path.join(tmpdir, 'datapackage.json'))
  errors = pkg.errors
  db_recover = datapackage.from_datapackage(tmpdir)
  shutil.rmtree(tmpdir)
  assert errors == [], errors
  assert db.index.spo == db_recover.index.spo, diff(db.index.spo, db_recover.index.spo)
