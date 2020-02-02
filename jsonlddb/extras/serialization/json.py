from jsonlddb import JsonLDDatabase
from jsonlddb.core import json, rdf

def dump(db, file):
  if type(file) == str:
    fw = open(file, 'w')
  else:
    fw = file
  #
  json.dump(db.index.spo, fw)
  return db

def load(file, db=None):
  if db is None:
    db = JsonLDDatabase()
  #
  if type(file) == str:
    fr = open(file, 'r')
  else:
    fr = file
  #
  db.update_triples(
    (
      rdf.RDFTerm(rdf.RDFTermType.IRI, s),
      p,
      rdf.RDFTerm(rdf.RDFTermType.LITERAL, o[0]) if isinstance(o, list) else rdf.RDFTerm(rdf.RDFTermType.IRI, o),
    )
    for s, pO in json.load(fr).items()
    for p, O in pO.items()
    for o in O
  )
  return db
