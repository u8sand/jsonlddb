from jsonlddb.core import chain_set

def assert_chain_set_eq(gen0, gen1):
  V0 = {}
  for v in gen0:
    if V0.get(v) is None:
      V0[v] = 0
    V0[v] += 1
  #
  V1 = {}
  for v in gen1:
    if V1.get(v) is None:
      V1[v] = 0
    V1[v] += 1
  #
  assert V0 == V1
  assert all(v == 1 for v in V0.values())

def test_chain_set_union():
  # only generators
  assert_chain_set_eq(
    chain_set.union([
      range(10),
      range(5, 15),
      range(10, 20),
    ]),
    range(20),
  )
  # 1 set mixture
  assert_chain_set_eq(
    chain_set.union([
      set(range(15, 25)),
      range(10),
      range(5, 15),
      range(10, 20),
    ]),
    range(25),
  )
  # 2 set mixture
  assert_chain_set_eq(
    chain_set.union([
      set(range(15, 25)),
      set(range(10)),
      range(5, 15),
      range(10, 20),
    ]),
    range(25),
  )
  # only sets
  assert_chain_set_eq(
    chain_set.union([
      set(range(10)),
      set(range(10, 20)),
    ]),
    range(20),
  )

def test_chain_set_intersection():
  # only generators
  assert_chain_set_eq(
    chain_set.intersection([
      range(10),
      range(5, 15),
    ]),
    set(range(5, 10)),
  )
  # 1 set mixture
  assert_chain_set_eq(
    chain_set.intersection([
      set(range(10)),
      range(5, 15),
    ]),
    set(range(5, 10)),
  )
  # 2 set mixture
  assert_chain_set_eq(
    chain_set.intersection([
      set(range(10)),
      set(range(5, 15)),
      range(0, 15),
    ]),
    set(range(5, 10)),
  )
  # only sets
  assert_chain_set_eq(
    chain_set.intersection([
      set(range(10)),
      set(range(5, 15)),
    ]),
    set(range(5, 10)),
  )
