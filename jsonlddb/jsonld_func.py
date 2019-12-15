from collections import namedtuple

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

class JsonLDIndex:
  def __init__(self, spo=dds(), pos=dds()):
    self.spo = spo
    self.pos = pos

def jsonld_to_triples(jsonld):
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
      yield (subj, pred, node_id)
      yield (subj, '*', node_id)
      for s in subjs:
        yield (s, '**', node_id)
    #
    # register this node's literals
    for p, o in node:
      yield (node_id, p, o)
    # add the remaining object relationships to Q to be processed in future iterations
    Q += [
      (subjs + [node_id], p, o)
      for p, O in obj.items()
      for o in (O if type(O) == list else [O])
      if not isLiteral(o)
    ]

def jsonld_index_insert_triples(triples, index = JsonLDIndex(spo=dds(), pos=dds())):
  for subj, pred, obj in triples:
    index.spo[subj][pred].add(obj)
    index.spo[obj]['~'+pred].add(subj)
    index.pos[pred][obj].add(subj)
    index.pos['~'+pred][subj].add(obj)
  return index

def jsonld_index_remove_triples(triples, index = JsonLDIndex(spo=dds(), pos=dds())):
  for subj, pred, obj in triples:
    index.spo[subj][pred].remove(obj)
    index.spo[obj]['~'+pred].remove(subj)
    index.pos[pred][obj].remove(subj)
    index.pos['~'+pred][subj].remove(obj)
  return index

def jsonld_frame_with_index(index, frame):
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
    subjs = set([subj for subj in index.spo.keys() if isIRI(subj)])
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
    s = index.pos[pred][obj]
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
      for o in jsonld_frame_with_index(index, obj)
      for subj in (
        index.pos[pred][o]
      )
    ])
    subjs = s if subjs is None else subjs & s
    if subjs == set():
      return set()
  #
  return set(index.spo.keys()) if subjs is None else subjs

def test_jsonld_frame_with_index():
  jsonld = [
    {
      '@id': '0',
      '@type': 'Person',
      'owns': {'@id': '4', '@type': 'Car', 'model': 'S'},
    },
    {
      '@id': '1',
      '@type': 'Person',
      'spouseOf': [{'@id': '0'}],
    },
    {
      '@id': '2',
      '@type': 'Person',
      'childOf': [{'@id': '0'}, {'@id': '1'}],
    },
    {
      '@id': '3',
      '@type': 'Person',
      'owns': {'@id': '5', '@type': 'Car', 'model': '3'},
      'childOf': [{'@id': '0'}, {'@id': '1'}],
    },
    {
      '@id': '6',
      '@type': 'Car',
      'model': 'X',
    },
  ]
  index = jsonld_index_insert_triples(jsonld_to_triples(jsonld))
  # Show all cars that are owned by a person
  query = {'@type': 'Car', '~owns': { '@type': 'Person' }}
  expected = {'4', '5'}
  result = jsonld_frame_with_index(index, query)
  assert result == expected, result

  # Show all cars that are owned by a person who is a child of another person who owns a car
  query = {'@type': 'Car', '~owns': {'@type': 'Person', 'childOf': { '@type': 'Person', 'owns': { '@type': 'Car' } }}}
  expected = {'5'}
  result = jsonld_frame_with_index(index, query)
  assert result == expected, result
