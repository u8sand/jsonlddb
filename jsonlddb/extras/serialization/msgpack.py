import msgpack
from jsonlddb import JsonLDDatabase
from jsonlddb.core import rdf, json

def dump(db, file):
  if type(file) == str:
    fw = open(file, 'wb')
  else:
    fw = file
  #
  packer = msgpack.Packer(encoding='utf-8')
  for s, po in json.prepare(db.index.spo).items():
    fw.write(packer.pack(s))
    fw.write(packer.pack(po))
  return db

def load(file, db=None):
  if db is None:
    db = JsonLDDatabase()
  #
  if type(file) == str:
    fr = open(file, 'rb')
  else:
    fr = file
  #
  unpacker = msgpack.Unpacker(fr, encoding='utf-8', use_list=False)
  db.update_triples(
    (
      rdf.RDFTerm(rdf.RDFTermType.IRI, s),
      p,
      rdf.RDFTerm(rdf.RDFTermType.LITERAL, o[0]) if isinstance(o, tuple) else rdf.RDFTerm(rdf.RDFTermType.IRI, o),
    )
    for s, pO in zip(unpacker, unpacker)
    for p, O in pO.items()
    for o in O
  )
  return db
