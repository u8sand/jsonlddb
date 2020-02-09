import itertools
import collections

dict_keys = type({}.keys())
def is_set(v):
  return type(v) in [set, dict_keys]

# These functions allow us to (hopefully efficiently) compute
#  set union/intersections on sets or iterators or both

def chain_set_union(generators):
  # Process sets first
  S = set()
  iterators = collections.deque()
  sets = collections.deque()
  for gen in generators:
    if is_set(gen):
      sets.append(gen)
    else:
      iterators.append(iter(gen))
  if len(sets) > 1:
    S.update(*sets)
  elif len(sets) == 1:
    S, = sets
  # No actual iterators? we're already done
  if not iterators:
    return S
  def G():
    # Yield what we got so far
    for s in S:
      yield s
    # Otherwise return a generator which yields the current elements
    while iterators:
      it = iterators.popleft()
      try:
        v = next(it)
        if v not in S:
          yield v
          S.add(v)
        iterators.append(it)
      except StopIteration:
        pass
  return G()

def chain_set_intersection(generators):
  # Process sets first
  S_ = None
  # Record element hashes that are missing from some of the sets
  i = itertools.count()
  iterators = collections.deque()
  sets = collections.deque()
  # Shortest to largest will be the most efficient way to process these
  for gen in generators:
    if is_set(gen):
      sets.append(gen)
    else:
      iterators.append((next(i), iter(gen)))
  if sets:
    S_ = set.intersection(*sets)
  else:
    S_ = set()
  # No actual iterators? just return the intersecting set
  if not iterators:
    return S_
  elif sets:
    impossible = set.union(*sets) - S_
  else:
    impossible = set()
  # Otherwise proceed with checking generators
  if S_:
    n_iterators = len(iterators) + 1
    S = {s: {-1} for s in S_}
  else:
    n_iterators = len(iterators)
    S = {}
  #
  def G():
    while iterators:
      i, it = iterators.popleft()
      try:
        v = next(it)
        # only if we know it's not impossible
        if v not in impossible:
          # create a new element if it doesn't yet exist
          if S.get(v) is None:
            S[v] = set()
          # has this iterator not registered this element yet?
          if i not in S[v]:
            S[v].add(i)
            # all generators registered--we can yield it
            if len(S[v]) == n_iterators:
              yield v
        iterators.append((i, it))
      except StopIteration:
        pass
  #
  return G()
