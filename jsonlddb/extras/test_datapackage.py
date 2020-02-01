import os
import tempfile
import shutil
from datapackage import DataPackage
from jsonlddb import JsonLDDatabase
from jsonlddb.extras import examples, datapackage

def test_to_datapackage():
  db = examples.familial_ownership
  tmpdir = tempfile.mkdtemp()
  datapackage.to_datapackage(db, tmpdir)
  pkg = DataPackage(os.path.join(tmpdir, 'datapackage.json'))
  errors = pkg.errors
  shutil.rmtree(tmpdir)
  assert errors == [], errors
