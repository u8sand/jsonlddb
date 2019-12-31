import enum
import logging
import itertools
import functools
import collections
import sortedcontainers
from .chain_set import chain_set_union, chain_set_intersection

@functools.total_ordering
class RDFTermType(enum.Enum):
  IRI = 0
  LITERAL = 1
  #
  def __lt__(self, other):
    return hash(self) < hash(other)
  #
  def __hash__(self):
    if self == RDFTermType.IRI:
      return 0
    elif self == RDFTermType.LITERAL:
      return 1

@functools.total_ordering
class RDFTerm:
  def __init__(self, type=None, value=None):
    self.type = type
    self.value = value
  #
  def __eq__(self, other):
    return (self.type, hash(type(self.value)), self.value) == (other.type, hash(type(other.value)), other.value)
  #
  def __lt__(self, other):
    return (self.type, hash(type(self.value)), self.value) < (other.type, hash(type(other.value)), other.value)
  #
  def __hash__(self):
    return hash((self.type, self.value))

def isLiteral(v):
  return type(v) not in [list, dict]

def collapse(v):
  return v[0] if type(v) == list and len(v) == 1 else v

def force_list(v):
  return v if type(v) == list else [v]

def canonical_uuid(j):
  import uuid, json
  return uuid.uuid5(uuid.UUID('00000000-0000-0000-0000-000000000000'), json.dumps(j))

def dds_insert(d, s, p, o):
  if d.get(s) is None:
    d[s] = {}
  if d[s].get(p) is None:
    d[s][p] = set()
  d[s][p].add(o)

def dds_remove(d, s, p, o):
  if d.get(s) is not None and d[s].get(p) is not None:
    d[s][p].remove(o)
    if not d[s][p]:
      del d[s][p]
      if not d[s]:
        del d[s]

class JsonLDIndex:
  def __init__(self, spo={}, pos={}):
    self.spo = spo
    self.pos = pos

def jsonld_to_triples(jsonld):
  Q = [
    ([], None, obj)
    for obj in (jsonld if type(jsonld) == list else [jsonld])
  ]
  while Q:
    subjs, pred, obj = Q.pop()
    if type(obj) != dict:
      if type(obj) == list:
        logging.warn('JSON-LD Formatting error, recovering by flattening list')
        Q += [
          (subjs, pred, o)
          for o in obj
        ]
        continue
      else:
        raise Exception(
          'Unrecoverable JSON-LD Formatting error, received type {}'.format(
            type(obj)
          )
        )
    # obtain distinguishing literals for this node
    node = [
      (p, o)
      for p, O in obj.items()
      if p != '@id'
      for o in (O if type(O) == list else [O])
      if isLiteral(o)
    ]
    # construct a canonical id for the node using the distinguishing literals
    existing_id = obj.get('@id')
    node_id = RDFTerm(
      RDFTermType.IRI,
      existing_id if existing_id is not None else canonical_uuid(node)
    )
    # register this relationship to its parent(s)
    if subjs:
      subj = subjs[-1]
      yield (subj, pred, node_id)
      yield (subj, '*', node_id)
      for s in subjs:
        yield (s, '**', node_id)
    #
    # register this node's literals
    for p, o in node:
      yield (node_id, p, RDFTerm(RDFTermType.LITERAL, o))
    # add the remaining object relationships to Q to be processed in future iterations
    Q += [
      (subjs + [node_id], p, o)
      for p, O in obj.items()
      for o in (O if type(O) == list else [O])
      if not isLiteral(o)
    ]

def jsonld_index_insert_triples(triples, index = JsonLDIndex()):
  for subj, pred, obj in triples:
    dds_insert(index.spo, subj, pred, obj)
    dds_insert(index.spo, obj, '~'+pred, subj)
    dds_insert(index.pos, pred, obj, subj)
    dds_insert(index.pos, '~'+pred, subj, obj)
  #
  return index

def jsonld_index_remove_triples(triples, index = JsonLDIndex()):
  for subj, pred, obj in triples:
    dds_remove(index.spo, subj, pred, obj)
    dds_remove(index.spo, obj, '~'+pred, subj)
    dds_remove(index.pos, pred, obj, subj)
    dds_remove(index.pos, '~'+pred, subj, obj)
  #
  return index

def pathset_from_object(obj):
  Q = [
    ([p], o)
    for p, O in obj.items()
    for o in force_list(O)
  ]
  while Q:
    path, obj = Q.pop()
    if type(obj) == dict and obj:
      Q += [
        (path + [p], o)
        for p, O in obj.items()
        for o in force_list(O)
      ]
    else:
      yield path, obj

def jsonld_resolve_frame_object(index, pred, obj):
  if pred in ['@id', '~@id']:
    subj = RDFTerm(RDFTermType.IRI, obj)
    return set([subj]) if subj in index.spo else set()
  if obj == {}:
    return chain_set_union(index.pos.get(pred, {}).values())
  else:
    return index.pos.get(pred, {}).get(RDFTerm(RDFTermType.LITERAL, obj), set())


def jsonld_frame_with_index(index, frame):
  '''
  This is the core of everything--the helper classes simply build off of
    frames.
  
  Here we use lambda for lazy evaluation; the result is that this function actually
   just prepares the necessary lookups, but we ultimately compute all intersections
   at the same time -- this should help with reducing the amount of memory
   being used as well as helping with CPU optimizations.

  TODO: Allow "options" with [] notation
  TODO: allow specifying minimal vs maximal subsets (currently always minimal)
  '''
  print('jsonld_frame', frame)
  # S looks like: (sizeof(path), path): lazy[possible_subjects]
  # sizeof(path) is what orders our dict.
  S = sortedcontainers.SortedDict()
  for path, obj in pathset_from_object(frame):
    key = (len(path[:-1]), tuple(path[:-1]))
    if S.get(key) is None:
      S[key] = lambda _p=path[-1], _o=obj: jsonld_resolve_frame_object(index, _p, _o)
    else:
      S[key] = lambda _p=path[-1], _o=obj, _s=S[key]: chain_set_intersection((_s(), jsonld_resolve_frame_object(index, _p, _o)))
  # Each iteration we pop one of the largest paths
  #  and intersect it with its parent, Once we get an
  #  empty path length we're done.
  while S:
    (L, path), subjs = S.popitem()
    if L == 0:
      return subjs()
    parent = tuple(path[:-1])
    pred = path[-1]
    #
    s = lambda _s=subjs, _p=pred: chain_set_union(
      index.pos.get(_p, {}).get(o, set())
      for o in _s()
    )
    if S.get(parent) is None:
      S[(L-1, parent)] = s
    else:
      S[(L-1, parent)] = lambda _s=S[(L-1, parent)], __s=s: chain_set_intersection((_s(), __s()))
  # If we got here, then S is empty, meaning the frame is empty,
  #  meaning we actually just want all subjects.
  return index.spo.keys()
