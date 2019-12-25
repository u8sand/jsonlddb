import itertools
import collections

dict_keys = type({}.keys())
def is_set(v):
  return type(v) in [set, dict_keys]

# These functions allow us to (hopefully efficiently) compute
#  set union/intersections on sets or iterators or both

def chain_set_union(generators):
  # Process sets first
  S_ = set()
  iterators = collections.deque()
  for gen in generators:
    if isinstance(gen, set):
      # Yield 'em as we get 'em
      for s in gen - S_:
        yield s
      S_ |= gen
    else:
      iterators.append(iter(gen))
  # No actual iterators? we're already done
  if not iterators:
    return
  # Otherwise return a generator which yields the current elements
  def G():
    S = S_
    # Proceed with yielding additional union elements
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
  #
  return G()

def chain_set_intersection(generators):
  # Process sets first
  S_ = None
  # Record element hashes that are missing from some of the sets
  impossible = set()
  i = itertools.count()
  iterators = collections.deque()
  # Shortest to largest will be the most efficient way to process these
  for gen in generators:
    if isinstance(gen, set):
      if S_ is None:
        S_ = gen
      else:
        impossible |= S_ - gen
        S_ &= gen
    else:
      iterators.append((next(i), iter(gen)))
  if S_ is None:
    S_ = set()
  # No actual iterators? just return the intersecting set
  if not iterators:
    return S_
  # Otherwise proceed with checking generators
  def G():
    S = {}
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
            if len(S[v]) == len(generators):
              yield v
        iterators.append((i, it))
      except StopIteration:
        pass
  #
  return G()
