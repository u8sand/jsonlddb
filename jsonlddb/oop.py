import logging
import itertools
from pprint import pformat
from jsonlddb.core import framing, jsonld, utils, index, rdf, json

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
          self._skip, None if self._limit is None else ((0 if self._skip is None else self._skip) + self._limit)
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
    if utils.isLiteral(pred):
      if pred == '@id':
        return self._subj
      else:
        # Find all objects that are children of this frame + predicate
        return JsonLDFrame(
          self._db,
          frame={ '~' + pred: self._frame },
          depth=self._depth - 1,
          additional=self._additional,
        )
    else:
      # Add more things to the frame
      return JsonLDFrame(
        self._db,
        frame=dict(self._frame, **pred),
        depth=self._depth - 1,
        additional=self._additional,
      )
  #
  def update(self, obj):
    if '@id' in obj and obj['@id'] != self._subj:
      raise Exception('Changing @id is not yet supported')
    self._db.index.insert_triples(
      jsonld.jsonld_to_triples(dict(obj, **{'@id': self._subj}))
    )
    return self
  #
  def remove(self, obj):
    self._db.index.remove_triples(
      jsonld.jsonld_to_triples(dict(obj, **{'@id': self._subj}))
    )
    return self
  #
  def keys(self):
    return {
      pred
      for index in [db.index for db in ([self._db] + self._additional)]
      for pred in index.spo.get(rdf.RDFTerm(rdf.RDFTermType.IRI, self._subj), {}).keys()
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
    return JsonLDNode(
      self._db, self._subj,
      frame=self._frame,
      skip=skip,
      limit=self._limit,
      depth=self._depth,
      additional=self._additional,
    )
  #
  def limit(self, limit):
    return JsonLDNode(
      self._db, self._subj,
      frame=self._frame,
      skip=self._skip,
      limit=limit,
      depth=self._depth,
      additional=self._additional,
    )
  #
  def depth(self, depth):
    return JsonLDNode(
      self._db, self._subj,
      frame=self._frame,
      skip=self._skip,
      limit=self._limit,
      depth=depth,
      additional=self._additional,
    )

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
        self, self._skip, None if self._limit is None else ((0 if self._skip is None else self._skip) + self._limit)
      )
    ]
    if len(vals) == 1:
      return vals[0]
    elif self._limit is not None and len(vals) >= self._limit:
      if self._skip is not None and self._skip > 0:
        return [ellipse, *vals, ellipse]
      else:
        return [*vals, ellipse]
    else:
      if self._skip is not None and self._skip > 0:
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
      return JsonLDFrame(
        self._db,
        frame={'~' + pred: self._frame},
        depth=self._depth,
        additional=self._additional
      )
    elif type(pred) == int:
      return next(iter(itertools.islice(self, pred, pred + 1)))
    elif type(pred) == slice:
      if pred.step is None or pred.step == 1 and (pred.start is None or pred.stop is None or pred.start < pred.stop):
        return self.skip(pred.start).limit(None if pred.stop is None else (pred.stop if pred.start is None else (pred.stop - pred.start)))
      else:
        return itertools.islice(self, pred.start, pred.stop, pred.step)
    else:
      # Add more things to the frame
      return JsonLDFrame(
        self._db,
        frame=dict(self._frame, **pred),
        depth=self._depth,
        additional=self._additional,
      )
  #
  def __iter__(self):
    for subj in self.frame(self._frame):
      if subj.type == rdf.RDFTermType.LITERAL or '~@id' in self._frame:
        yield subj.value
      else:
        yield JsonLDNode(
          self._db, subj.value,
          frame=self._frame,
          depth=self._depth,
          additional=self._additional,
        )
  #
  def __len__(self):
    return sum(
      1 for _ in self.frame(self._frame)
    )
  #
  def skip(self, skip):
    return JsonLDFrame(
      self._db,
      frame=self._frame,
      skip=skip,
      limit=self._limit,
      depth=self._depth,
      additional=self._additional,
    )
  #
  def limit(self, limit):
    return JsonLDFrame(
      self._db,
      frame=self._frame,
      skip=self._skip,
      limit=limit,
      depth=self._depth,
      additional=self._additional,
    )
  #
  def depth(self, depth):
    return JsonLDFrame(
      self._db, self._frame,
      skip=self._skip,
      limit=self._limit,
      depth=depth,
      additional=self._additional,
    )
  #
  def with_db(self, db):
    return JsonLDFrame(
      self._db,
      frame=self._frame,
      skip=self._skip,
      limit=self._limit,
      depth=self._depth,
      additional=self._additional + [db],
    )
  #
  def frame(self, frame):
    return framing.jsonld_frame_with_multi_index(
      [
        db.index
        for db in ([self._db] + self._additional)
      ], frame.get('~@id', frame)
    )
  #
  def update(self, obj):
    self._db.index.insert_triples(
      triples
      for subj in self.frame(self._frame) if subj.type == rdf.RDFTermType.IRI
      for triples in jsonld.jsonld_to_triples(dict(obj, **{'@id': subj.value}))
    )
    return self
  #
  def remove(self, obj):
    self._db.index.remove_triples(
      triples
      for subj in self.frame(self._frame) if subj.type == rdf.RDFTermType.IRI
      for triples in jsonld.jsonld_to_triples(dict(obj, **{'@id': subj.value}))
    )
    return self


class JsonLDDatabase(JsonLDFrame):
  def __init__(self):
    JsonLDFrame.__init__(self, self, {})
    self.index = index.JsonLDIndex()
  #
  def insert(self, obj):
    self.index.insert_triples(jsonld.jsonld_to_triples(obj))
    return self
  #
  def update(self, obj):
    logging.warning('Deprecated: use insert when adding data to a database and update to apply to a framed selection.')
    return self.insert(obj)
  #
  def dump(self, file, fmt='msgpack'):
    from jsonlddb.extras import serialization
    return getattr(serialization, fmt).dump(self, file)
  #
  def load(self, file, fmt='msgpack'):
    from jsonlddb.extras import serialization
    return getattr(serialization, fmt).load(file, db=self)
