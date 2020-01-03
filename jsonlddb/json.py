import json
import functools

def default_ex(o):
  ''' Properly serialize JSON objects
  '''
  if isinstance(o, JSON):
    return o.value
  return o

loads = json.loads
dumps = functools.partial(json.dumps, default=default_ex)

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
