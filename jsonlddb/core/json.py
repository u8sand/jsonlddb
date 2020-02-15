import json
from jsonlddb.core import rdf

def prepare(o):
  ''' Properly serialize JSON objects
  '''
  if isinstance(o, JSON):
    return prepare(o.value)
  elif isinstance(o, rdf.Term):
    if o.type == rdf.TermType.IRI:
      return str(o.value)
    else:
      return [o.value]
  elif isinstance(o, dict):
    return {
      prepare(k): prepare(v)
      for k, v in o.items()
    }
  elif isinstance(o, list) or isinstance(o, set) or isinstance(o, tuple):
    return [
      prepare(v)
      for v in o
    ]
  else:
    return o

load = json.load
loads = json.loads
dump = lambda obj, fp, **kwargs: json.dump(prepare(obj), fp, **kwargs)
dumps = lambda obj, **kwargs: json.dumps(prepare(obj), **kwargs)

class JSON(object):
  ''' Use an object normally in python with awareness that it should
  be json, allowing us to hash/serialize it using json methods.
  '''
  def __init__(self, value):
    self.value = value
  #
  def __str__(self):
    return dumps(self.value)
  #
  def __hash__(self):
    return hash(dumps(self.value))
  #
  def __repr__(self):
    return repr(self.value)
  #
  def get(self, k):
    return self.value.get(k)
  #
  def __getitem__(self, k):
    return self.value[k]
  #
  def __setitem__(self, k, v):
    self.value[k] = v
  #
  def __eq__(self, other):
    if isinstance(other, JSON):
      return self.value == other.value
    return self.value == other
  #
  def __getattribute__(self, attr):
    try:
      return object.__getattribute__(self, attr)
    except:
      return self.value.__getattribute__(attr)
