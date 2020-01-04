import itertools
from pprint import pformat
from jsonlddb.core import *

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
  def __init__(self, db, subj, frame={}, skip=0, limit=10, depth=3, additional=[]):
    self._db = db
    self._subj = subj
    self._frame = dict(frame, **{ '@id': subj })
    self._skip = skip
    self._limit = limit
    self._depth = depth
    self._additional = additional
  #
  def _repr(self):
    if '~@id' in self._frame:
      return self._subj
    else:
      return dict({
        pred: objs._repr() if isinstance(objs, JsonLDFrame) else objs
        for pred, objs in itertools.islice(
          self.items(),
          self._skip, None if self._limit is None else (self._skip + self._limit)
        )
      }) if self._depth else ellipse
  #
  def __repr__(self):
    return pformat(self._repr())
  #
  def __str__(self):
    return str(self._repr())
  #
  def __getitem__(self, pred):
    if isLiteral(pred):
      if pred == '@id':
        return self._subj
      else:
        # Find all objects that are children of this frame + predicate
        return JsonLDFrame(self._db, frame={ '~' + pred: self._frame }, depth=self._depth - 1, additional=self._additional)
    else:
      # Add more things to the frame
      return JsonLDFrame(self._db, frame=dict(self._frame, **pred), depth=self._depth - 1, additional=self._additional)
  #
  def keys(self):
    return {
      pred
      for index in [db.index for db in ([self._db] + self._additional)]
      for pred in index.spo.get(RDFTerm(RDFTermType.IRI, self._subj), {}).keys()
      if pred not in ['*', '**'] and not pred.startswith('~')
    }
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
          depth=self._depth - 1,
          additional=self._additional
        )
  #
  def items(self):
    return zip(self.keys(), self.values())
  #
  def skip(self, skip):
    return JsonLDNode(self._db, self._subj, self._frame, skip, self._limit, self._depth, additional=self._additional)
  #
  def limit(self, limit):
    return JsonLDNode(self._db, self._subj, self._frame, self._skip, limit, self._depth, additional=self._additional)
  #
  def depth(self, depth):
    return JsonLDNode(self._db, self._subj, self._frame, self._skip, self._limit, depth, additional=self._additional)

class JsonLDFrame:
  ''' Represent a frame, providing the ability to observe and interact
  with the complete set of all nodes which satisfy the frame.
  '''
  def __init__(self, db, frame={}, skip=0, limit=10, depth=4, additional=[]):
    self._db = db
    self._frame = frame
    self._skip = skip
    self._limit = limit
    self._depth = depth
    self._additional = additional
  #
  def _repr(self):
    if not self._depth:
      return ellipse
    vals = [
      obj._repr() if getattr(obj, '_repr', None) is not None else obj
      for obj in itertools.islice(
        self, self._skip, None if self._limit is None else (self._skip + self._limit)
      )
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
    if type(pred) == str:
      return JsonLDFrame(self._db, frame={'~' + pred: self._frame}, depth=self._depth, additional=self._additional)
    elif type(pred) == int:
      return next(iter(itertools.islice(self, pred, pred + 1)))
    elif type(pred) == slice:
      if pred.step is None or pred.step == 1 and (pred.start is None or pred.stop is None or pred.start < pred.stop):
        return self.skip(pred.start).limit(None if pred.stop is None else pred.stop - pred.start)
      else:
        return itertools.islice(self, pred.start, pred.stop, pred.step)
    else:
      # Add more things to the frame
      return JsonLDFrame(self._db, frame=dict(self._frame, **pred), depth=self._depth, additional=self._additional)
  #
  def __iter__(self):
    for subj in self.frame(self._frame):
      if subj.type == RDFTermType.IRI:
        yield JsonLDNode(self._db, subj.value, frame=self._frame, depth=self._depth, additional=self._additional)
      else:
        yield subj.value
  #
  def skip(self, skip):
    return JsonLDFrame(self._db, self._frame, skip, self._limit, self._depth, additional=self._additional)
  #
  def limit(self, limit):
    return JsonLDFrame(self._db, self._frame, self._skip, limit, self._depth, additional=self._additional)
  #
  def depth(self, depth):
    return JsonLDFrame(self._db, self._frame, self._skip, self._limit, depth, additional=self._additional)
  #
  def with_db(self, db):
    return JsonLDFrame(self._db, self._frame, self._skip, self._limit, self._depth, additional=self._additional + [db])
  #
  def frame(self, frame):
    return jsonld_frame_with_multi_index(
      [
        db.index
        for db in ([self._db] + self._additional)
      ], frame
    )

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
    jsonld_index_insert_triples(self.index, triples)
    return self
  #
  def remove_triples(self, triples):
    jsonld_index_remove_triples(self.index, triples)
    return self
