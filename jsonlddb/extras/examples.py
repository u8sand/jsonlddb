from jsonlddb import JsonLDDatabase

familial_ownership = [
  {
    '@id': '0',
    '@type': 'Person',
    'owns': {'@id': '4', '@type': 'Car', 'model': 'S'},
    'spouseOf': [{'@id': '1'}],
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
