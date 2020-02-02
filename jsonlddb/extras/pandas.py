import json
import logging
import itertools
import pandas as pd
from jsonlddb.oop import JsonLDDatabase, JsonLDNode
from jsonlddb.core import utils

def from_dfs(dfs, rels=()):
  '''
  dfs:  Data frames key, name of table, value pandas dataframe
  rels: A list of relationship definitions
    M2M: dict(
      through=table_name,
      through_subject=through table col for subject id,
      through_object=through table col for object id,
      subject=table for subject,
      predicate=field in subject for this relationship,
      object=table for object,
    )
    O2M: dict(
      subject=table for subject,
      predicate=field in subject for this relationship,
      object=table for object,
    )
  '''
  m2m = {}
  o2m = {}
  for rel in rels:
    if rel.get('through'):
      m2m[rel['through']] = rel
    else:
      if o2m.get(rel['subject']) is None:
        o2m[rel['subject']] = set()
      o2m[rel['subject']].add((rel['predicate'], rel['object']))
  #
  def _generate():
    for tbl, df in dfs.items():
      if tbl in m2m:
        rel = m2m[tbl]
        for _, record in df.iterrows():
          jsonld_record = dict({
            '@id': record[rel['through_subject']],
            '@type': rel['subject'],
            rel['predicate']: {
              '@id': record[rel['through_object']],
              '@type': rel['object']
            }
          })
          yield jsonld_record
      else:
        for record_index, record in df.iterrows():
          jsonld_record = dict({ '@id': record_index }, **record.dropna().to_dict())
          jsonld_record['@type'] = tbl
          if tbl in o2m:
            for pred, obj in o2m[tbl]:
              if jsonld_record.get(pred):
                jsonld_record[pred] = {
                  '@id': jsonld_record[pred],
                  '@type': obj
                }
          yield jsonld_record
  #
  db = JsonLDDatabase()
  db.insert(list(_generate()))
  return db

def to_dfs(db):
  dfs = {}
  ids = {}
  for tbl in db['@type']:
    if dfs.get(tbl) is None:
      dfs[tbl] = {}
    for record in db[{'@type': tbl}]:
      for pred, objs in record.items():
        if pred == '@type':
          continue
        if dfs[tbl].get(pred) is None:
          dfs[tbl][pred] = {}
        if len(objs) > 1:
          if all(map(utils.isLiteral, objs)):
            dfs[tbl][pred][record['@id']] = json.dumps(objs)
            continue
          elif all(map(utils.isLiteral, objs)):
            logging.warning('Ignoring mixed literals on same predicate with objects')
          ftbls = set(objs['@type'])
          for ftbl in ftbls:
            m2m = tbl+'__'+pred+'_'+ftbl
            if dfs.get(m2m) is None:
              dfs[m2m] = { tbl: {}, pred+'_'+ftbl: {} }
              ids[m2m] = iter(itertools.count())
            for obj in objs[{'@type': ftbl}]:
              r2r = next(ids[m2m])
              dfs[m2m][tbl][r2r] = record['@id']
              dfs[m2m][pred+'_'+ftbl][r2r] = obj['@id']
        elif utils.isLiteral(objs[0]):
          dfs[tbl][pred][record['@id']] = objs[0]
        else:
          dfs[tbl][pred][record['@id']] = objs[0]['@id']
  return {
    tbl: pd.DataFrame(df).rename_axis(index='@id', columns=None)
    for tbl, df in dfs.items()
  }

