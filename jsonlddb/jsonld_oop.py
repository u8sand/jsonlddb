from .jsonld_func import *
from pprint import pformat

def isIRI(v):
  import uuid
  return isinstance(v, uuid.UUID)

def isLiteral(v):
  return type(v) not in [list, dict]

def collapse(v):
  return v[0] if type(v) == list and len(v) == 1 else v

def force_list(v):
  return v if type(v) == list else [v]

def canonical_uuid(j):
  import uuid, json
  return uuid.uuid5(uuid.UUID('00000000-0000-0000-0000-000000000000'), json.dumps(j))

class Ellipse:
  def __repr__(self):
    return '...'
  def __str__(self):
    return '...'
ellipse = Ellipse()

class JsonLDNode:
  ''' Represents a single node, providing the ability to observe and interact
  with the complete set of all relationships to this node abiding by the frame.
  '''
  def __init__(self, db, subj, frame={}):
    self._db = db
    self._subj = subj
    self._frame = dict(frame, **{ '@id': subj })
  #
  def _repr(self, depth):
    if '~@id' in self._frame:
      return self._subj
    else:
      return dict({
        pred: JsonLDFrame(
          self._db,
          {
            '~' + pred: { '@id': self._subj },
          }
        )._repr(depth - 1)
        for pred, objs in self._db._spo[self._subj].items()
        if pred not in ['@id', '*', '**'] and not pred.startswith('~')
      }, **{
        '@id': self._subj
      }) if depth else ellipse
  #
  def __repr__(self):
    return pformat(self._repr(3))
  #
  def __str__(self):
    return str(self._repr(3))
  #
  def __getitem__(self, subj):
    if isLiteral(subj):
      if subj == '@id':
        return self._subj
      else:
        # Find all objects that are children of this frame + predicate
        return JsonLDFrame(self._db, { '~' + subj: self._frame })
    else:
      # Add more things to the frame
      return JsonLDFrame(self._db, dict(self._frame, **subj))

class JsonLDFrame:
  ''' Represent a frame, providing the ability to observe and interact
  with the complete set of all nodes which satisfy the frame.
  '''
  def __init__(self, db, frame={}):
    self._db = db
    self._frame = frame
  #
  def _repr(self, depth, maxlen=6):
    if not depth:
      return ellipse
    vals = [
      obj._repr(depth - 1) if getattr(obj, '_repr', None) is not None else obj
      for obj in itertools.islice(self, None, maxlen)
    ]
    if len(vals) == 1:
      return vals[0]
    elif len(vals) == maxlen:
      return [*vals, ellipse]
    else:
      return vals
  #
  def __repr__(self):
    return pformat(self._repr(4))
  #
  def __str__(self):
    return str(self._repr(4))
  #
  def __getitem__(self, subj):
    if isIRI(subj):
      # Select a given subject retaining the current frame
      return JsonLDNode(self._db, subj, self._frame)
    elif isLiteral(subj):
      if subj == '@id':
        return collapse([
          subj
          for subj in self._db.frame(self._frame)
          if isIRI(subj)
        ])
      else:
        # Find all objects that are children of this frame + predicate
        return JsonLDFrame(self._db, { '~' + subj: self._frame })
    else:
      # Add more things to the frame
      return JsonLDFrame(self._db, dict(self._frame, **subj))
  #
  def __iter__(self):
    if not self._frame:
      for subj in self._db._spo.keys():
        if isIRI(subj):
          yield JsonLDNode(self._db, subj)
        else:
          yield subj
    elif '@id' in self._frame:
      yield JsonLDNode(self._db, self._frame['@id'], self._frame)
    else:
      for subj in self._db.frame(self._frame):
        if isIRI(subj):
          yield JsonLDNode(self._db, subj, self._frame)
        else:
          yield subj

class JsonLDDatabase(JsonLDFrame):
  def __init__(self):
    JsonLDFrame.__init__(self, self, {})
    self.index = JsonLDIndex()
  #
  def update(self, jsonld):
    self.update_triples(jsonld_to_triples(jsonld))
  #
  def update_triples(self, triples):
    jsonld_index_insert_triples(triples, index=self.index)
  #
  def remove_triples(self, triples):
    jsonld_index_remove_triples(triples, index=self.index)
  #
  def frame(self, frame):
    return jsonld_frame_with_index(self.index, frame)
