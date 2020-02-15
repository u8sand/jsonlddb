import functools
import sortedcontainers
from jsonlddb.core import utils, chain_set, rdf

def _resolve_index_po(index, pred=None):
  return index.pos.get(pred, {}).values()

def _resolve_index_pos(index, pred=None, obj=None):
  return index.pos.get(pred, {}).get(obj, set())

def _resolve_frame_object_with_multi_index(multi_index, pred, obj):
  if pred == '@id':
    subj = rdf.Term(rdf.TermType.IRI, obj)
    # return {subj} if any(subj in index.spo for index in multi_index) else set()
    return chain_set.Iterable(({subj},))
  #
  if isinstance(obj, rdf.Term):
    return \
      multi_index \
      .map(functools.partial(_resolve_index_pos, pred=pred, obj=obj))
  elif obj == {}:
    return \
      multi_index \
        .map(functools.partial(_resolve_index_po, pred=pred)) \
      .chain()
  else:
    return \
      multi_index \
      .map(functools.partial(_resolve_index_pos, pred=pred, obj=rdf.Term(rdf.TermType.LITERAL, obj)))

def with_multi_index(multi_index, frame):
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
  multi_index = chain_set.Iterable(multi_index)

  for path, obj in utils.pathset_from_object(frame):
    key = (len(path[:-1]), tuple(path[:-1]))
    s = \
      chain_set.Iterable(utils.force_list(obj)) \
        .map(
          functools.partial(
            _resolve_frame_object_with_multi_index,
            multi_index,
            path[-1]
          )
        ) \
        .chain() \
      .chain_union()
    if S.get(key) is None:
      S[key] = s
    else:
      S[key] = S[key].intersection(s)
  #
  # Each iteration we pop one of the largest paths
  #  and intersect it with its parent, Once we get an
  #  empty path length we're done.
  while S:
    (L, path), subjs = S.popitem()
    if L == 0:
      return subjs()
    parent = tuple(path[:-1])
    #
    s = \
      subjs \
        .map(
          functools.partial(
            _resolve_frame_object_with_multi_index,
            multi_index,
            path[-1],
          )
        ) \
        .chain() \
      .chain_union()
    if S.get((L-1, parent)) is None:
      S[(L-1, parent)] = s
    else:
      S[(L-1, parent)] = S[(L-1, parent)].intersection(s)
  # If we got here, then S is empty, meaning the frame is empty,
  #  meaning we actually just want all subjects.
  return multi_index.map(lambda index: index.spo.keys()).chain_union()()
