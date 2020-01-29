import uuid
import enum
import logging
import collections
import sortedcontainers
from jsonlddb import json
from jsonlddb.chain_set import chain_set_union, chain_set_intersection
from jsonlddb.index import JsonLDIndex
from jsonlddb.rdf import RDFTerm, RDFTermType

def isLiteral(v):
  return type(v) in [type(None), str, int, float, bool, uuid.UUID, RDFTerm]

def force_list(v):
  return v if type(v) == list else [v]

def canonical_uuid(j):
  return uuid.uuid5(uuid.UUID('00000000-0000-0000-0000-000000000000'), json.dumps(j))

def jsonld_to_triples(jsonld):
  Q = [
    ([], None, obj)
    for obj in (jsonld if type(jsonld) == list else [jsonld])
  ]
  warned = False
  while Q:
    subjs, pred, obj = Q.pop()
    if type(obj) != dict:
      if type(obj) == list:
        if not warned:
          logging.warning('JSON-LD Formatting error, recovering by flattening list')
          warned = True
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
    existing_id = None
    literals = []
    relationships = []
    for p, O in obj.items():
      for o in force_list(O):
        if p == '@id':
          assert existing_id is None, 'Only one @id is acceptable'
          existing_id = o
        elif isLiteral(o):
          literals.append((p, o))
        elif type(o) == dict and list(o.keys()) == ['@value']: # Force treat object as literal
          literals.append((p, json.JSON(o['@value'])))
        else:
          relationships.append((p, o))
    # construct a canonical id for the node using the distinguishing literals
    node_id = RDFTerm(
      RDFTermType.IRI,
      existing_id if existing_id is not None else canonical_uuid(literals)
    )
    # register this relationship to its parent(s)
    if subjs:
      subj = subjs[-1]
      yield (subj, pred, node_id)
      # yield (subj, '*', node_id)
      # for s in subjs:
      #   yield (s, '**', node_id)
    #
    # register this node's literals
    for p, o in literals:
      yield (node_id, p, RDFTerm(RDFTermType.LITERAL, o))
    # add the remaining object relationships to Q to be processed in future iterations
    Q += [
      (subjs + [node_id], p, o)
      for p, o in relationships
    ]

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

def jsonld_resolve_frame_object_with_multi_index(multi_index, pred, obj):
  if pred == '@id':
    subj = RDFTerm(RDFTermType.IRI, obj)
    return {subj} if any(subj in index.spo for index in multi_index) else set()
  if obj == {}:
    return chain_set_union(subjs for index in multi_index for subjs in index.pos.get(pred, {}).values())
  else:
    return chain_set_union(
      index.pos.get(pred, {}).get(RDFTerm(RDFTermType.LITERAL, obj), set())
      for index in multi_index
    )

def jsonld_frame_with_multi_index(multi_index, frame):
  '''
  This is the core of everything--the helper classes simply build off of
    frames.
  
  Here we use lambda for lazy evaluation; the result is that this function actually
   just prepares the necessary lookups, but we ultimately compute all intersections
   at the same time -- this should help with reducing the amount of memory
   being used as well as helping with CPU optimizations.
  '''
  # S looks like: (sizeof(path), path): lazy[possible_subjects]
  # sizeof(path) is what orders our dict.
  S = sortedcontainers.SortedDict()
  for path, obj in pathset_from_object(frame):
    key = (len(path[:-1]), tuple(path[:-1]))
    s = lambda _p=path[-1], _o=force_list(obj): chain_set_union(
      jsonld_resolve_frame_object_with_multi_index(multi_index, _p, o)
      for o in _o
    )
    if S.get(key) is None:
      S[key] = s
    else:
      S[key] = lambda _s=s, __s=S[key]: chain_set_intersection((_s(), __s()))
  #
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
      for index in multi_index
      for o in _s()
    )
    if S.get((L-1, parent)) is None:
      S[(L-1, parent)] = s
    else:
      S[(L-1, parent)] = lambda _s=S[(L-1, parent)], __s=s: chain_set_intersection((_s(), __s()))
  # If we got here, then S is empty, meaning the frame is empty,
  #  meaning we actually just want all subjects.
  return chain_set_union(
    index.spo.keys()
    for index in multi_index
  )
