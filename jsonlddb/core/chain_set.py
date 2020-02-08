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

class Lazy:
  def __init__(self, val=None):
    self._val = val
  #
  def __repr__(self):
    if isinstance(self._val, Lazy):
      return '{}[{}]'.format(self.__class__.__name__, repr(self._val))
    else:
      return '{}[{}]'.format(self.__class__.__name__, type(self._val).__name__)
  #
  def __call__(self):
    val = self._val
    while isinstance(val, Lazy):
      val = val()
    return val
  #
  def map(self, func):
    return Map(func, self)
  #
  def chain(self):
    return ChainIterable(self)
  #
  def union(self, other):
    return Iterable((self, other)).chain_union()
  #
  def intersection(self, other):
    return Iterable((self, other)).chain_intersection()
  #
  def chain_union(self):
    return ChainUnion(self)
  #
  def chain_intersection(self):
    return ChainIntersection(self)

class Map(Lazy):
  def __init__(self, func, it):
    super().__init__()
    self._func = func
    self._it = it
  #
  def __repr__(self):
    return 'Map[{}, {}]'.format(
      self._func.__name__,
      repr(self._it) if isinstance(self._it, Lazy) else '...'
    )
  #
  def __call__(self):
    it = self._it
    while isinstance(it, Lazy):
      it = it()
    for val in it:
      while isinstance(val, Lazy):
        val = val()
      ret = self._func(val)
      while isinstance(ret, Lazy):
        ret = ret()
      yield ret

class ChainUnion(Lazy):
  def __call__(self):
    return chain_set_union(super().__call__())

class ChainIntersection(Lazy):
  def __call__(self):
    return chain_set_intersection(super().__call__())

class ChainIterable(Lazy):
  def __call__(self):
    for it in super().__call__():
      while isinstance(it, Lazy):
        it = it()
      for val in it:
        while isinstance(val, Lazy):
          val = val()
        yield val

class CompleteSet(Lazy):
  pass

class Set(Lazy):
  pass

class Iterable(Lazy):
  def __call__(self):
    for val in super().__call__():
      while isinstance(val, Lazy):
        val = val()
      yield val
