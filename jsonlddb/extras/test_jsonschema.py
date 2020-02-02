from jsonschema import RefResolver, Draft6Validator
from jsonlddb import JsonLDDatabase
from jsonlddb.extras import generate, jsonschema

def test_to_jsonschema():
  jsonld = list(generate.random_jsonld(100, 5, 2, 5, 2, 5))
  db = JsonLDDatabase().insert(jsonld)
  schemas = jsonschema.to_jsonschema(db)
  resolver = RefResolver.from_schema(schemas)
  validators = {}
  for component, schema in schemas['components'].items():
    validators[component] = Draft6Validator(schema, resolver=resolver)
  #
  for instance in jsonld:
    validators[instance['@type']].validate(instance)
