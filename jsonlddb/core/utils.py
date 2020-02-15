import uuid
from jsonlddb.core import json, rdf, chain_set

def isLiteral(v):
  if type(v) in [type(None), str, int, float, bool, uuid.UUID, rdf.Term, json.JSON]:
    return True
  if type(v) == dict and '@value' in v:
    return True
  return False

def force_list(v):
  return v if type(v) == list else [v]

def canonical_uuid(j):
  return uuid.uuid5(uuid.UUID('00000000-0000-0000-0000-000000000000'), json.dumps(j))

def pathset_from_object(obj):
  Q = [
    ([p], o)
    for p, o in obj.items()
  ]
  while Q:
    path, obj = Q.pop()
    if type(obj) == dict and obj:
      Q += [
        (path + [p], o)
        for p, o in obj.items()
      ]
    else:
      yield path, obj
