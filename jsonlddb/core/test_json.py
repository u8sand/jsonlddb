import json
from jsonlddb.core import json as jsonlddb_json

def test_json():
  json_test = {
    'a': 'b',
    'c': [{'d': 'e'}, 'f'],
    'g': 0,
  }
  json_test_obj = jsonlddb_json.JSON(dict(**json_test))
  json_test['g'] += 1
  json_test_obj['g'] = 1
  assert json_test_obj == jsonlddb_json.JSON(json_test)
  assert json_test_obj == json_test
  assert str(jsonlddb_json.JSON(json_test)) == json.dumps(json_test)
  assert repr(json_test_obj) == repr(json_test)
  assert hash(json_test_obj) == hash(jsonlddb_json.JSON(jsonlddb_json.loads(jsonlddb_json.dumps(json_test_obj))))
