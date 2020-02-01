import re
import os
import functools
import collections
from jsonlddb.core import json, utils

def to_datapackage(db, path='datapackage'):
  ''' Create frictionless datapackage from jsonlddb database
  path: directory to creeate the package,
        if None will just return schema and not write data.
  '''
  #
  schema = {
    'profile': 'tabular-data-package',
    'resources': [],
  }
  preds = {
    p
    for p, os in db.index.pos.items()
    if not re.match(r'^[~@]', p)
  }
  m2ms = set()
  # create main resources
  for tbl in db['@type']:
    resource = {
      'profile': 'tabular-data-resource',
      'name': tbl.lower(),
      'description': tbl,
      'path': tbl.lower() + '.tsv',
      'format': 'tsv',
      'mediatype': 'text/tsv',
      'encoding': 'utf-8',
      'schema': {
        'fields': [
          {
            'name': '@id',
            'type': 'string',
            'required': True,
          }
        ],
        'missingValues': [''],
        'primaryKey': ['@id'],
        'foreignKeys': [],
      }
    }
    for pred in preds:
      pyTypes = {(utils.isLiteral(v), type(v)) for v in db[{'@type': tbl}][pred]}
      field = {
        'name': pred,
        # 'rdfType': db.context + pred,
      }
      n_pyTypes = len(pyTypes - {(True, type(None))})
      if n_pyTypes == 0:
        continue
      elif n_pyTypes == 1:
        isLiteral, pyType = next(iter(pyTypes))
        if isLiteral:
          if pyType == str:
            field['type'] = 'string'
          elif pyType == int:
            field['type'] = 'integer'
          elif pyType == float:
            field['type'] = 'number'
          elif pyType == bool:
            field['type'] = 'boolean'
          else:
            field['type'] = 'object'
        else:
          objs = db[{'@type': tbl}]
          ftbls = set(objs[pred]['@type'])
          for ftbl in ftbls:
            if any(len(record[pred][{'@type': ftbl}]) > 1 for record in objs):
              # m2m
              m2m = tbl+'__'+pred+'_'+ftbl
              m2ms.add((
                m2m,
                (tbl, tbl),
                (ftbl, pred+'_'+ftbl),
              ))
              resource['schema']['foreignKeys'].append({
                'fields': pred,
                'reference': {
                  'resource': m2m,
                  'fields': tbl,
                }
              })
            else:
              # o2o/o2m
              resource['schema']['foreignKeys'].append({
                'fields': pred,
                'reference': {
                  'resource': ftbl,
                  'fields': '@id',
                }
              })
            #
          #
        #
      else:
        field['type'] = 'any'
      #
      if type(None) not in pyTypes:
        field['required'] = True
      else:
        field['required'] = False
      #
      resource['schema']['fields'].append(field)
    #
    if not resource['schema']['foreignKeys']:
      del resource['schema']['foreignKeys']
    schema['resources'].append(resource)
  # create many-to-many tables
  for tbl, (left_tbl, left_field), (right_tbl, right_field) in m2ms:
    schema['resources'].append({
      'profile': 'tabular-data-resource',
      'name': tbl.lower(),
      'description': tbl,
      'path': tbl.lower() + '.tsv',
      'format': 'tsv',
      'mediatype': 'text/tsv',
      'encoding': 'utf-8',
      'schema': {
        'fields': [
          {
            'name': left_field,
            'type': 'string',
            'required': True,
          },
          {
            'name': right_field,
            'type': 'string',
            'required': True,
          }
        ],
        'missingValues': [''],
        'primaryKey': [left_field, right_field],
        'foreignKeys': [
          {
            'fields': left_field,
            'reference': {
              'resource': left_tbl,
              'fields': '@id',
            }
          },
          {
            'fields': right_field,
            'reference': {
              'resource': right_tbl,
              'fields': '@id',
            }
          },
        ],
      }
    })
  # if path is set, write to disk
  if path:
    os.makedirs(path, exist_ok=True)
    from jsonlddb.extras import pandas
    for tbl, df in pandas.to_dfs(db).items():
      df.to_csv(os.path.join(path, tbl+'.tsv'), sep='\t')
    json.dump(schema, open(os.path.join(path, 'datapackage.json'), 'w'), indent=2)
  #
  return schema

