import pytest
from jsonlddb.core import jsonld_to_triples
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
  with pytest.raises(Exception):
    list(jsonld_to_triples({
      'k': {1, 2},
    }))
