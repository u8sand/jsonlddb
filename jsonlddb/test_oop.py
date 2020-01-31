from jsonlddb.oop import JsonLDDatabase
from jsonlddb.extras import examples

def test_jsonlddb_framing():
  db = examples.familial_ownership

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
  index = db.update({
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
