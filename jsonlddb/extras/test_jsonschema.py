from jsonlddb import JsonLDDatabase
from jsonlddb.extras import generate, jsonschema

def test_to_jsonschema():
  db = JsonLDDatabase().update(list(generate.random_jsonld(100, 5, 2, 5, 2, 5)))
  jsonschema.to_jsonschema(db)
