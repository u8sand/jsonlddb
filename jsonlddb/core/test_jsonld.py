import pytest
from jsonlddb.core import jsonld, rdf

def test_jsonld_triple_conversion():
  # Recoverable double list success
  assert set(jsonld.to_triples({
    '@id': '0',
    'v': [[{ '@id': '1' }, { '@id': '2' }]],
  })) == {
    (rdf.Term(rdf.TermType.IRI, '0'), 'v', rdf.Term(rdf.TermType.IRI, '1')),
    (rdf.Term(rdf.TermType.IRI, '0'), 'v', rdf.Term(rdf.TermType.IRI, '2')),
  }
  # Automatic literal-based uuid deduplication
  triples = set(jsonld.to_triples([
    { 'a': 'b', 'c': { 'a': 'd' } },
    { 'a': 'd', 'c': { 'a': 'b' } },
  ]))
  subjs = {subj for subj, _, _ in triples}
  assert len(subjs) == 2
  a, b = subjs
  assert triples == {
    (a, 'c', b),
    (b, 'c', a),
    (a, 'a', rdf.Term(rdf.TermType.LITERAL, 'b')),
    (b, 'a', rdf.Term(rdf.TermType.LITERAL, 'd')),
  } or triples == {
    (a, 'c', b),
    (b, 'c', a),
    (a, 'a', rdf.Term(rdf.TermType.LITERAL, 'd')),
    (b, 'a', rdf.Term(rdf.TermType.LITERAL, 'b')),
  }
  # Unrecoverable invalid type raises
  with pytest.raises(Exception):
    list(jsonld.to_triples({
      'k': {1, 2},
    }))
