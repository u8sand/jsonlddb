from jsonlddb.extras.generate import random_jsonld
from jsonlddb.oop import JsonLDDatabase

def test_generate():
  jsonld = list(random_jsonld(10, 5, 1, 5, 1, 5))
  assert len(jsonld) == 10
  db = JsonLDDatabase()
  db.update(jsonld)
  assert len(list(db['@type'])) <= 5
