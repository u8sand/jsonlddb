import json
from jsonlddb.json import JSON, loads, dumps

def test_json():
  json_test = {
    'a': 'b',
    'c': [{'d': 'e'}, 'f'],
    'g': 0,
  }
  json_test_obj = JSON(dict(**json_test))
  json_test['g'] += 1
  json_test_obj['g'] = 1
  assert json_test_obj == JSON(json_test)
  assert json_test_obj == json_test
  assert str(JSON(json_test)) == json.dumps(json_test)
  assert repr(json_test_obj) == repr(json_test)
  assert hash(json_test_obj) == hash(JSON(loads(dumps(json_test_obj))))
