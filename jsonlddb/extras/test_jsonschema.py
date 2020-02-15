from jsonschema import RefResolver, Draft6Validator
from jsonlddb import JsonLDDatabase
from jsonlddb.extras import generate, jsonschema, examples

def test_to_jsonschema_example():
  jsonld = examples.familial_ownership
  db = JsonLDDatabase().insert(jsonld)
  schemas = jsonschema.to_jsonschema(db)
  resolver = RefResolver.from_schema(schemas)
  validators = {}
  for component, schema in schemas['components'].items():
    validators[component] = Draft6Validator(schema, resolver=resolver)
  #
  for instance in jsonld:
    validators[instance['@type']].validate(instance)

def test_to_jsonschema_random():
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
