from jsonlddb import JsonLDDatabase
from jsonlddb.extras import examples, dispatch

def test_dispatch():
  db = JsonLDDatabase().insert([
    {
      '@type': 'Thing',
      'url': 'test1',
    },
    {
      '@type': 'Thing',
      'name': 'test2',
    },
  ])
  #
  ctx = dispatch.JsonLDDispatch()
  @ctx.register(
    given={
      '@type': 'Thing',
      'url': {},
    },
    produce={
      '@type': 'Thing',
      'name': {},
    },
  )
  def test(given):
    return { '@id': given['@id'], 'name': 'test!' }
  #
  assert 'test!' in ctx.frame(db, {'@type': 'Thing'})['name']
