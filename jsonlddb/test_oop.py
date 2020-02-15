import tempfile
from jsonlddb.oop import JsonLDDatabase
from jsonlddb.extras import examples

try:
  from jsondiff import diff
except ImportError:
  import logging
  logging.warning('install jsondiff for easier debugging')
  diff = lambda a, b: str((a, b))

def test_jsonlddb():
  db = JsonLDDatabase().insert(examples.familial_ownership)
  print(repr(db))
  print(str(db))
  print(repr(db[0]))
  print(str(db[0]))
  print(db.skip(1).limit(1).depth(1))
  print(db[0].skip(1).limit(1).depth(1))
  print(db[:])
  print(db[:2])
  print(db[1:])
  print(db[1:3])
  print(db[0:3:2])

  # Empty query should return all subjects
  query = {}
  expected = {'0', '1', '2', '3', '4', '5', '6'}
  result = set(db[query]['@id'])
  assert result == expected, result

  # Literal should expand to ~ {}
  expected = {'Car', 'Person'}
  result = set(db['@type']['@id'])
  assert result == expected, result

  # Show all cars that are owned by a person
  query = {'@type': 'Car', '~owns': { '@type': 'Person' }}
  expected = {'4', '5'}
  result = set(db[query]['@id'])
  assert result == expected, result

  # Show all cars that are owned by a person who is a child of another person who owns a car
  query = {'@type': 'Car', '~owns': {'@type': 'Person', 'childOf': { '@type': 'Person', 'owns': { '@type': 'Car' } }}}
  expected = {'5'}
  result = set(db[query]['@id'])
  assert result == expected, result

  # Someone who is the spouse of someone who owns something
  #  and is the parent of someone that owns something
  query = { '~spouseOf': { 'owns': {} }, '~childOf': { 'owns': {} } }
  expected = {'1'}
  result = set(db[query]['@id'])
  assert result == expected, result

  # Move car ownership of person 3 to person 2
  index = db.remove({
    '@id': '3',
    'owns': { '@id': '5' }
  })
  index = db.insert({
    '@id': '2',
    'owns': { '@id': '5' }
  })
  # Assert that it worked
  query = { '@type': 'Person', 'owns': { '@id': '5' } }
  expected = {'2'}
  result = set(db[query]['@id'])
  assert result == expected, result

  # Query all car models that are owned
  query = { '~model': { '@type': 'Car', '~owns': {} } }
  expected = {'S', '3'}
  result = set(db[query])
  assert result == expected, result

  # Query models S and X
  query = { '@type': 'Car', 'model': ['S', 'X'] }
  expected = {'4', '6'}
  result = set(db[query]['@id'])
  assert result == expected

  # Update frame
  db[{'@type': 'Person', '~childOf': {}}].update({
    'parent': True,
  })
  expected = {'0', '1'}
  result = set(db[{'@type': 'Person', 'parent': True}]['@id'])
  assert result == expected

  # Update node
  db[{'@id': '6'}][0].update({ 'year': '2015' })
  expected = {'6'}
  result = set(db[{'year': '2015'}]['@id'])
  assert result == expected

  # Remove this pred-value pair from anything
  db.remove({ 'year': '2015' })
  expected = set()
  result = set(db[{'year': {}}]['@id'])
  assert result == expected

  # Ensure serialization/deserialization works
  tmp = tempfile.mktemp()
  db.dump(tmp)
  db_recover = JsonLDDatabase().load(tmp)
  assert db.index.spo == db_recover.index.spo, diff(db.index.spo, db_recover.index.spo)
