import itertools
from pprint import pformat
from .core import *

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
  def __init__(self, db, subj, frame={}, skip=0, limit=10, depth=3):
    self._db = db
    self._subj = subj
    self._frame = dict(frame, **{ '@id': subj })
    self._skip = skip
    self._limit = limit
    self._depth = depth
  #
  def _repr(self):
    if '~@id' in self._frame:
      return self._subj
    else:
      return dict({
        pred: objs._repr() if isinstance(objs, JsonLDFrame) else objs
        for pred, objs in itertools.islice(
          self.items(),
          self._skip, self._skip + self._limit
        )
      }) if self._depth else ellipse
  #
  def __repr__(self):
    return pformat(self._repr(3))
  #
  def __str__(self):
    return str(self._repr(3))
  #
  def __getitem__(self, pred):
    if isLiteral(pred):
      if pred == '@id':
        return self._subj
      else:
        # Find all objects that are children of this frame + predicate
        return JsonLDFrame(self._db, frame={ '~' + pred: self._frame }, skip=self._skip, limit=self._limit, depth=self._depth - 1)
    else:
      # Add more things to the frame
      return JsonLDFrame(self._db, frame=dict(self._frame, **pred), skip=self._skip, limit=self._limit, depth=self._depth - 1)
  #
  def keys(self):
    return set(
      pred
      for pred in self._db.index.spo[RDFTerm(RDFTermType.IRI, self._subj)].keys()
      if pred not in ['*', '**'] and not pred.startswith('~')
    )
  #
  def values(self):
    for pred in self.keys():
      if pred == '@id':
        yield self._subj
      else:
        yield JsonLDFrame(
          self._db,
          frame={
            '~' + pred: self._frame,
          },
          skip=self._skip, limit=self._limit, depth=self._depth - 1
        )
  #
  def items(self):
    return zip(self.keys(), self.values())

class JsonLDFrame:
  ''' Represent a frame, providing the ability to observe and interact
  with the complete set of all nodes which satisfy the frame.
  '''
  def __init__(self, db, frame={}, skip=0, limit=10, depth=4):
    self._db = db
    self._frame = frame
    self._skip = skip
    self._limit = limit
    self._depth = depth
  #
  def _repr(self):
    if not self._depth:
      return ellipse
    vals = [
      obj._repr() if getattr(obj, '_repr', None) is not None else obj
      for obj in itertools.islice(self, self._skip, self._skip + self._limit)
    ]
    if len(vals) == 1:
      return vals[0]
    elif len(vals) >= self._limit:
      if self._skip > 0:
        return [ellipse, *vals, ellipse]
      else:
        return [*vals, ellipse]
    else:
      if self._skip > 0:
        return [ellipse, *vals]
      else:
        return vals
  #
  def __repr__(self):
    return pformat(self._repr())
  #
  def __str__(self):
    return str(self._repr())
  #
  def __getitem__(self, pred):
    if isLiteral(pred):
      return JsonLDFrame(self._db, frame={'~' + pred: self._frame}, skip=self._skip, limit=self._limit, depth=self._depth)
    else:
      # Add more things to the frame
      return JsonLDFrame(self._db, frame=dict(self._frame, **pred), skip=self._skip, limit=self._limit, depth=self._depth)
  #
  def __iter__(self):
    for subj in self._db.frame(self._frame):
      if subj.type == RDFTermType.IRI:
        yield JsonLDNode(self._db, subj.value, frame=self._frame, skip=self._skip, limit=self._limit, depth=self._depth - 1)
      else:
        yield subj.value
  #
  def skip(self, skip):
    return JsonLDFrame(self._db, self._frame, skip, self._limit, self._depth)
  #
  def limit(self, limit):
    return JsonLDFrame(self._db, self._frame, self._skip, limit, self._depth)
  #
  def depth(self, depth):
    return JsonLDFrame(self._db, self._frame, self._skip, self._limit, depth)

class JsonLDDatabase(JsonLDFrame):
  def __init__(self):
    JsonLDFrame.__init__(self, self, {})
    self.index = JsonLDIndex()
  #
  def update(self, jsonld):
    self.update_triples(jsonld_to_triples(jsonld))
    return self
  #
  def update_triples(self, triples):
    jsonld_index_insert_triples(triples, index=self.index)
    return self
  #
  def remove_triples(self, triples):
    jsonld_index_remove_triples(triples, index=self.index)
    return self
  #
  def frame(self, frame):
    return jsonld_frame_with_index(self.index, frame)
