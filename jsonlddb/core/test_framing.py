import pytest
from jsonlddb.core import jsonld, rdf

def test_jsonld_triple_conversion():
  # Recoverable double list success
  assert set(jsonld.jsonld_to_triples({
    '@id': '0',
    'v': [[{ '@id': '1' }, { '@id': '2' }]],
  })) == {
    (rdf.RDFTerm(rdf.RDFTermType.IRI, '0'), 'v', rdf.RDFTerm(rdf.RDFTermType.IRI, '1')),
    (rdf.RDFTerm(rdf.RDFTermType.IRI, '0'), 'v', rdf.RDFTerm(rdf.RDFTermType.IRI, '2')),
  }
  # Automatic literal-based uuid deduplication
  triples = set(jsonld.jsonld_to_triples([
    { 'a': 'b', 'c': { 'a': 'd' } },
    { 'a': 'd', 'c': { 'a': 'b' } },
  ]))
  subjs = {subj for subj, _, _ in triples}
  assert len(subjs) == 2
  a, b = subjs
  assert triples == {
    (a, 'c', b),
    (b, 'c', a),
    (a, 'a', rdf.RDFTerm(rdf.RDFTermType.LITERAL, 'b')),
    (b, 'a', rdf.RDFTerm(rdf.RDFTermType.LITERAL, 'd')),
  } or triples == {
    (a, 'c', b),
    (b, 'c', a),
    (a, 'a', rdf.RDFTerm(rdf.RDFTermType.LITERAL, 'd')),
    (b, 'a', rdf.RDFTerm(rdf.RDFTermType.LITERAL, 'b')),
  }
  # Unrecoverable invalid type raises
  with pytest.raises(Exception):
    list(jsonld.jsonld_to_triples({
      'k': {1, 2},
    }))
