from uuid import UUID
from jsonlddb import JsonLDDatabase

db = JsonLDDatabase()

# Add JsonLD to the database
db.update({
  '@type': 'Dataset',
  'name': 'My Data',
  'storedIn': {
    '@type': 'Dataset',
    'name': 'Our Data',
    'createdBy': {
      '@type': 'Person',
      'name': 'Me'
    }
  },
  'createdBy': {
    '@type': 'Person',
    'name': 'Me'
  }
})

# Add additional JsonLD (note that both `{ @type: Person, name: Me }`
#  and `{ @type: Dataset, name: My Data }` do not get duplicated)
db.update({
  '@type': 'Person',
  'name': 'Me',
  'likes': {
    '@type': 'Dataset',
    'name': 'My Data'
  }
})

# Show the name of all datasets
db[{ '@type': 'Dataset' }]['name']

# Show me all the creators of datasets
db[{ '~createdBy': {'@type': 'Dataset'} }]

# Show me all names (of anything)
db['name']
