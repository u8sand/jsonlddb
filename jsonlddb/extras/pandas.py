import logging
import itertools
import pandas as pd
from jsonlddb.oop import JsonLDDatabase, JsonLDNode
from jsonlddb.core import utils, json

def from_dfs(dfs, rels={}):
  '''
  dfs:  Data frames key, name of table, value pandas dataframe
  rels: relationship definitions
    Mo2Mo (Many objects to many objects): dict(
      through=table_name,
      through_subject=through table col for subject id,
      through_object=through table col for object id,
      subject=table for subject,
      predicate=field in subject for this relationship,
      object=table for object,
    )
    Oo2Mo (One objects to many objects): dict(
      subject=table for subject,
      predicate=field in subject for this relationship,
      object=table for object,
    )
    Oo2Mv (One objects to many values): dict(
      through=table_name,
      through_subject=through table col for subject id,
      through_object=through table col for value,
      subject=table for subject,
      predicate=field in subject for this relationship,
    )
  '''
  mo2mo = {}
  oo2mo = {}
  oo2mv = {}
  for rel in rels.get('Mo2Mo', []):
    mo2mo[rel['through']] = rel
  for rel in rels.get('Oo2Mo', []):
    if oo2mo.get(rel['subject']) is None:
      oo2mo[rel['subject']] = set()
    oo2mo[rel['subject']].add((rel['predicate'], rel['object']))
  for rel in rels.get('Oo2Mv', []):
    oo2mv[rel['through']] = rel
  #
  def _generate():
    for tbl, df in dfs.items():
      if tbl in mo2mo:
        rel = mo2mo[tbl]
        for _, record in df.iterrows():
          jsonld_record = dict({
            '@id': record[rel['through_subject']],
            '@type': rel['subject'],
            rel['predicate']: {
              '@id': record[rel['through_object']],
              '@type': rel['object'],
            },
          })
          yield jsonld_record
      elif tbl in oo2mv:
        rel = oo2mv[tbl]
        for _, record in df.iterrows():
          jsonld_record = dict({
            '@id': record[rel['through_subject']],
            '@type': rel['subject'],
            rel['predicate']: record[rel['through_object']],
          })
          yield jsonld_record
      else:
        for record_index, record in df.iterrows():
          jsonld_record = dict({ '@id': record_index }, **{
            k: v if utils.isLiteral(v) else {'@value': v}
            for k, v in record.dropna().to_dict().items()
            if v
          })
          jsonld_record['@type'] = tbl
          if tbl in oo2mo:
            for pred, obj in oo2mo[tbl]:
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
        if len(objs) > 1:
          if all(map(utils.isLiteral, objs)):
            # o2m
            o2m = tbl+'__'+pred
            if dfs.get(o2m) is None:
              dfs[o2m] = { tbl: {}, pred: {} }
              ids[o2m] = iter(itertools.count())
            for obj in objs:
              r2r = next(ids[o2m])
              dfs[o2m][tbl][r2r] = record['@id']
              dfs[o2m][pred][r2r] = obj
          elif any(map(utils.isLiteral, objs)):
            logging.warning('Ignoring mixed literals on same predicate with objects')
          else:
            ftbls = set(objs['@type'])
            for ftbl in ftbls:
              mo2mo = tbl+'__'+pred+'_'+ftbl
              if dfs.get(mo2mo) is None:
                dfs[mo2mo] = { tbl: {}, pred+'_'+ftbl: {} }
                ids[mo2mo] = iter(itertools.count())
              for obj in objs[{'@type': ftbl}]:
                r2r = next(ids[mo2mo])
                dfs[mo2mo][tbl][r2r] = record['@id']
                dfs[mo2mo][pred+'_'+ftbl][r2r] = obj['@id']
        elif utils.isLiteral(objs[0]):
          if dfs[tbl].get(pred) is None:
            dfs[tbl][pred] = {}
          dfs[tbl][pred][record['@id']] = objs[0]
        else:
          if dfs[tbl].get(pred) is None:
            dfs[tbl][pred] = {}
          dfs[tbl][pred][record['@id']] = objs[0]['@id']
  return {
    tbl: pd.DataFrame(df).rename_axis(index='@id', columns=None)
    for tbl, df in dfs.items()
  }

