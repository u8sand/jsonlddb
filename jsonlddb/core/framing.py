import sortedcontainers
from jsonlddb.core import utils, chain_set, rdf

def jsonld_resolve_frame_object_with_multi_index(multi_index, pred, obj):
  if pred == '@id':
    subj = rdf.RDFTerm(rdf.RDFTermType.IRI, obj)
    return {subj} if any(subj in index.spo for index in multi_index) else set()
  if obj == {}:
    return chain_set.chain_set_union(subjs for index in multi_index for subjs in index.pos.get(pred, {}).values())
  else:
    return chain_set.chain_set_union(
      index.pos.get(pred, {}).get(rdf.RDFTerm(rdf.RDFTermType.LITERAL, obj), set())
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
  for path, obj in utils.pathset_from_object(frame):
    key = (len(path[:-1]), tuple(path[:-1]))
    s = lambda _p=path[-1], _o=utils.force_list(obj): chain_set.chain_set_union(
      jsonld_resolve_frame_object_with_multi_index(multi_index, _p, o)
      for o in _o
    )
    if S.get(key) is None:
      S[key] = s
    else:
      S[key] = lambda _s=s, __s=S[key]: chain_set.chain_set_intersection((_s(), __s()))
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
    s = lambda _s=subjs, _p=pred: chain_set.chain_set_union(
      index.pos.get(_p, {}).get(o, set())
      for index in multi_index
      for o in _s()
    )
    if S.get((L-1, parent)) is None:
      S[(L-1, parent)] = s
    else:
      S[(L-1, parent)] = lambda _s=S[(L-1, parent)], __s=s: chain_set.chain_set_intersection((_s(), __s()))
  # If we got here, then S is empty, meaning the frame is empty,
  #  meaning we actually just want all subjects.
  return chain_set.chain_set_union(
    index.spo.keys()
    for index in multi_index
  )
