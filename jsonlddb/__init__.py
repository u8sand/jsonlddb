'''
This Json LD Database and other convenient classes should prove very
 useful with loading in JsonLD and actually using it. It identifies
 nodes that are the same and ensures they are treated the same. It
 exposes a mechanism of access resembling a large set of json objects
 while saving duplication only once and enabling circular referencing.

It is quite computationally efficient using hashtables and sets to
 quickly narrow down and satisfy frames (at the cost of a good amount of
 nested hash tables -- $2*(S*(2*P)*O)$ literals). For many operations
 including Json LD Framing this results in query satisfaction bound only
 by the (deep) size of your frame (likely quite small).

While perhaps space-prohibitive for large amounts of data, for small to
 mid-ranged amounts of data like what I anticipate to use this for
 (Json-LD Dispatch), this approach will have no extensive negative
 performance impacts.

It works somewhat intuitively--allowing you to access the database as you
 might a json object--using frames for selection.

Important assumptions made by this architecture:
  - Unless an @id is specified, literals--not connections--are
    used to distinguish any given node.
  - In the case that an @id is specified with different literals,
    those literals will be merged into a single object.
  - Strong Json-LD Structure is enforced (i.e. values are lists)
    ({ '@id': subj, 'pred': [{...}], ... })

'''

from pprint import pformat
import json
import itertools


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

class defaultdict(dict):
  ''' A defaultdict that works as anticipated when nested
  at the cost of potentially constructing empty values while reading.

  https://gist.github.com/u8sand/1b6ae223b6333ab2d9ea37fa67094a98
  '''
  def __init__(self, _default, **kwargs):
    super().__init__(self, **kwargs)
    self._default = _default

  def __getitem__(self, k):
    if k not in self:
      self[k] = self._default()
    return super().__getitem__(k)

def ds(**kwargs):
  return defaultdict(set, **kwargs)

def dds(**kwargs):
  return defaultdict(ds, **kwargs)

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
    self._spo = dds()
    self._pos = dds()
  #
  def update(self, jsonld):
    Q = [
      ([], None, obj)
      for obj in (jsonld if type(jsonld) == list else [jsonld])
    ]
    while Q:
      subjs, pred, obj = Q.pop()
      assert type(obj) == dict, 'JSON-LD Formatting error'
      # obtain distinguishing literals for this node
      node = [
        (p, o)
        for p, O in obj.items()
        if p != '@id'
        for o in (O if type(O) == list else [O])
        if isLiteral(o)
      ]
      # construct a canonical id for the node using the distinguishing literals
      node_id = obj.get('@id', canonical_uuid(node))
      # register this relationship to its parent(s)
      if subjs:
        subj = subjs[-1]
        self.update_triples([
          (subj, pred, node_id),
          (subj, '*', node_id),
        ] + [
          (s, '**', node_id)
          for s in subjs
        ])

      # register this node's literals
      self.update_triples([
        (node_id, p, o)
        for p, o in node
      ])
      # add the remaining object relationships to Q to be processed in future iterations
      Q += [
        (subjs + [node_id], p, o)
        for p, O in obj.items()
        for o in (O if type(O) == list else [O])
        if not isLiteral(o)
      ]
  #
  def update_triples(self, triples):
    for subj, pred, obj in triples:
      self._spo[subj][pred].add(obj)
      self._spo[obj]['~'+pred].add(subj)
      self._pos[pred][obj].add(subj)
      self._pos['~'+pred][subj].add(obj)
  #
  def remove_triples(self, triples):
    for subj, pred, obj in triples:
      self._spo[subj][pred].remove(obj)
      self._spo[obj]['~'+pred].remove(subj)
      self._pos[pred][obj].remove(subj)
      self._pos['~'+pred][subj].remove(obj)
  #
  def frame(self, frame):
    '''
    This is the core of everything--the helper classes simply build off of
      frames.

    TODO: Allow "options" with [] notation
    TODO: Eliminate recursion (not too difficult, probably makes ^ easier)
    TODO: allow specifying minimal vs maximal subsets (currently always minimal)
    '''
    if '@id' in frame:
      subjs = set([frame['@id']])
      del frame['@id']
    elif '~@id' in frame:
      subjs = set([subj for subj in self._spo.keys() if isIRI(subj)])
      del frame['~@id']
    else:
      subjs = None
    #
    # this frame
    # O(deep_frame)
    conds = [
      (pred, obj)
      for pred, objs in frame.items()
      for obj in force_list(objs)
      if isLiteral(obj)
    ]
    # O(deep_frame) * O(n_subjs)
    for pred, obj in conds:
      # O(1)
      s = self._pos[pred][obj]
      subjs = s if subjs is None else subjs & s # O(min(subjs, s))
      if subjs == set():
        return set()
    #
    # deep frame
    deep_conds = [
      (pred, obj)
      for pred, objs in frame.items()
      for obj in force_list(objs)
      if type(obj) == dict
    ]
    for pred, obj in deep_conds:
      s = set([
        subj
        for o in self.frame(obj)
        for subj in (
          self._pos[pred][o]
        )
      ])
      subjs = s if subjs is None else subjs & s
      if subjs == set():
        return set()
    #
    return set(self._spo.keys()) if subjs is None else subjs
