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
  def __init__(self, spo=None, pos=None):
    self.spo = {} if spo is None else spo
    self.pos = {} if pos is None else pos
  #
  def insert_triples(self, triples):
    for subj, pred, obj in triples:
      dds_insert(self.spo, subj, pred, obj)
      # dds_insert(self.spo, obj, '~'+pred, subj)
      dds_insert(self.pos, pred, obj, subj)
      dds_insert(self.pos, '~'+pred, subj, obj)
    #
    return self
  #
  def remove_triples(self, triples):
    for subj, pred, obj in triples:
      dds_remove(self.spo, subj, pred, obj)
      # dds_remove(self.spo, obj, '~'+pred, subj)
      dds_remove(self.pos, pred, obj, subj)
      dds_remove(self.pos, '~'+pred, subj, obj)
    #
    return self
