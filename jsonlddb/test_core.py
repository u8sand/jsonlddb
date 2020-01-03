from nose.tools import assert_raises
from jsonlddb.core import jsonld_frame_with_index, jsonld_index_insert_triples, jsonld_to_triples, jsonld_index_remove_triples, JsonLDIndex
from jsonlddb.rdf import RDFTerm, RDFTermType

def test_jsonld_triple_conversion():
  # Recoverable double list success
  assert set(jsonld_to_triples({
    '@id': '0',
    'v': [[{ '@id': '1' }, { '@id': '2' }]],
  })) == {
    (RDFTerm(RDFTermType.IRI, '0'), 'v', RDFTerm(RDFTermType.IRI, '1')),
    (RDFTerm(RDFTermType.IRI, '0'), 'v', RDFTerm(RDFTermType.IRI, '2')),
  }
  # Automatic literal-based uuid deduplication
  triples = set(jsonld_to_triples([
    { 'a': 'b', 'c': { 'a': 'd' } },
    { 'a': 'd', 'c': { 'a': 'b' } },
  ]))
  subjs = {subj for subj, _, _ in triples}
  assert len(subjs) == 2
  a, b = subjs
  assert triples == {
    (a, 'c', b),
    (b, 'c', a),
    (a, 'a', RDFTerm(RDFTermType.LITERAL, 'b')),
    (b, 'a', RDFTerm(RDFTermType.LITERAL, 'd')),
  } or triples == {
    (a, 'c', b),
    (b, 'c', a),
    (a, 'a', RDFTerm(RDFTermType.LITERAL, 'd')),
    (b, 'a', RDFTerm(RDFTermType.LITERAL, 'b')),
  }
  # Unrecoverable invalid type raises
  with assert_raises(Exception):
    list(jsonld_to_triples({
      'k': {1, 2},
    }))

def test_jsonld_frame_with_index():
  jsonld = [
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
  index = jsonld_index_insert_triples(JsonLDIndex(), jsonld_to_triples(jsonld))

  # Empty query should return all subjects
  query = {}
  expected = index.spo.keys()
  result = set(jsonld_frame_with_index(index, query))
  assert result == expected, result

  # Show all cars that are owned by a person
  query = {'@type': 'Car', '~owns': { '@type': 'Person' }}
  expected = {RDFTerm(RDFTermType.IRI, '4'), RDFTerm(RDFTermType.IRI, '5')}
  result = set(jsonld_frame_with_index(index, query))
  assert result == expected, result

  # Show all cars that are owned by a person who is a child of another person who owns a car
  query = {'@type': 'Car', '~owns': {'@type': 'Person', 'childOf': { '@type': 'Person', 'owns': { '@type': 'Car' } }}}
  expected = {RDFTerm(RDFTermType.IRI, '5')}
  result = set(jsonld_frame_with_index(index, query))
  assert result == expected, result

  # Someone who is the spouse of someone who owns something
  #  and is the parent of someone that owns something
  query = { '~spouseOf': { 'owns': {} }, '~childOf': { 'owns': {} } }
  expected = {RDFTerm(RDFTermType.IRI, '1')}
  result = set(jsonld_frame_with_index(index, query))
  assert result == expected, result

  # Move car ownership of person 3 to person 2
  index = jsonld_index_remove_triples(index, jsonld_to_triples({
    '@id': '3',
    'owns': { '@id': '5' }
  }))
  index = jsonld_index_insert_triples(index, jsonld_to_triples({
    '@id': '2',
    'owns': { '@id': '5' }
  }))
  # Assert that it worked
  query = { '@type': 'Person', 'owns': { '@id': '5' } }
  expected = {RDFTerm(RDFTermType.IRI, '2')}
  result = set(jsonld_frame_with_index(index, query))
  assert result == expected, result

  # Query all car models that are owned
  query = { '~model': { '@type': 'Car', '~owns': {} } }
  expected = {RDFTerm(RDFTermType.LITERAL, 'S'), RDFTerm(RDFTermType.LITERAL, '3')}
  result = set(jsonld_frame_with_index(index, query))
  assert result == expected, result
