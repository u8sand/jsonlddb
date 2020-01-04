from jsonlddb.oop import JsonLDDatabase
from jsonlddb.rules import frame_with_rules

def test_rules():
  context = {
    'function:test': lambda ld: { '@id': ld['@id'], 'name': 'test!' },
  }
  rules = JsonLDDatabase().update([
    {
      '@type': 'Rule',
      'given': {
        '@value': {
          '@type': 'Thing',
          'url': {},
        }
      },
      'using': 'function:test',
      'produce': {
        '@value': {
          '@type': 'Thing',
          'name': {},
        }
      }
    }
  ])
  docs = JsonLDDatabase().update([
    {
      '@type': 'Thing',
      'url': 'test1',
    },
    {
      '@type': 'Thing',
      'name': 'test2',
    },
  ])
  # Relevant query, should resolve
  assert 'test!' in frame_with_rules(docs, { '@type': 'Thing' }, rules=rules, context=context)['name']
  # Too broad, shouldn't resolve
  assert 'test!' not in frame_with_rules(docs, {}, rules=rules, context=context)['name']
