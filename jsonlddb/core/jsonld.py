import logging
from jsonlddb.core import utils, rdf, json

def to_triples(jsonld):
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
      for o in utils.force_list(O):
        if p == '@id':
          assert existing_id is None, 'Only one @id is acceptable'
          existing_id = o
        elif utils.isLiteral(o):
          literals.append((p, o))
        elif type(o) == dict and list(o.keys()) == ['@value']: # Force treat object as literal
          literals.append((p, json.JSON(o['@value'])))
        else:
          relationships.append((p, o))
    # construct a canonical id for the node using the distinguishing literals
    node_id = rdf.Term(
      rdf.TermType.IRI,
      existing_id if existing_id is not None else utils.canonical_uuid(literals)
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
      yield (node_id, p, rdf.Term(rdf.TermType.LITERAL, o))
    # add the remaining object relationships to Q to be processed in future iterations
    Q += [
      (subjs + [node_id], p, o)
      for p, o in relationships
    ]
