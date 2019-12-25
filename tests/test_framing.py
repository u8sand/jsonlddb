from jsonlddb.core import jsonld_index_insert_triples, jsonld_to_triples, jsonld_frame_with_index

def test_jsonld_frame_with_index():
  jsonld = [
    {
      '@id': '0',
      '@type': 'Person',
      'owns': {'@id': '4', '@type': 'Car', 'model': 'S'},
    },
    {
      '@id': '1',
      '@type': 'Person',
      'spouseOf': [{'@id': '0'}],
    },
    {
      '@id': '2',
      '@type': 'Person',
      'childOf': [{'@id': '0'}, {'@id': '1'}],
    },
    {
      '@id': '3',
      '@type': 'Person',
      'owns': {'@id': '5', '@type': 'Car', 'model': '3'},
      'childOf': [{'@id': '0'}, {'@id': '1'}],
    },
    {
      '@id': '6',
      '@type': 'Car',
      'model': 'X',
    },
  ]
  index = jsonld_index_insert_triples(jsonld_to_triples(jsonld))
  # Show all cars that are owned by a person
  query = {'@type': 'Car', '~owns': { '@type': 'Person' }}
  expected = {'4', '5'}
  result = jsonld_frame_with_index(index, query)
  assert result == expected, result

  # Show all cars that are owned by a person who is a child of another person who owns a car
  query = {'@type': 'Car', '~owns': {'@type': 'Person', 'childOf': { '@type': 'Person', 'owns': { '@type': 'Car' } }}}
  expected = {'5'}
  result = jsonld_frame_with_index(index, query)
  assert result == expected, result
