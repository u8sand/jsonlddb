import re
import os
import functools
import collections
import pandas as pd
from datapackage import DataPackage
from jsonlddb.core import json, utils
from jsonlddb.extras import pandas

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
  o2ms = set()
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
      objs = db[{'@type': tbl}]
      pyTypes = {(utils.isLiteral(v), type(v)) for v in objs[pred]}
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
            fieldType = 'string'
          elif pyType in [int, float]:
            # NaNs need to be float even if they
            #  are integers for pandas..
            fieldType = 'number'
          elif pyType == bool:
            fieldType = 'boolean'
          else:
            fieldType = 'any'
          #
          if any(len(record[pred]) > 1 for record in objs):
            # o2m
            o2m = tbl+'__'+pred
            o2ms.add((
              o2m, tbl, pred, fieldType
            ))
            # don't create field
            field = None
          else:
            field['type'] = fieldType
        else:
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
              # don't create field
              field = None
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
      if field is not None:
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
  # create many to ones
  for tbl, left_tbl, pred, fieldType in o2ms:
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
            'name': left_tbl,
            'type': 'string',
            'required': True,
          },
          {
            'name': pred,
            'type': fieldType,
            'required': True,
          }
        ],
        'missingValues': [''],
        'primaryKey': [left_tbl, pred],
        'foreignKeys': [
          {
            'fields': left_tbl,
            'reference': {
              'resource': left_tbl,
              'fields': '@id',
            }
          },
        ],
      }
    })
  # if path is set, write to disk
  if path:
    os.makedirs(path, exist_ok=True)
    dfs = pandas.to_dfs(db)
    for resource in schema['resources']:
      cols = [field['name'] for field in resource['schema']['fields']]
      dfs[resource['description']].reset_index()[cols].to_csv(
        os.path.join(path, resource['path']),
        sep='\t',
        index=None,
      )
    json.dump(schema, open(os.path.join(path, 'datapackage.json'), 'w'), indent=2)
  #
  return schema

def from_datapackage(path):
  if os.path.isdir(path):
    path = os.path.join(path, 'datapackage.json')
  #
  pkg = DataPackage(path)
  dfs = {}
  rels = { 'Mo2Mo': [], 'Oo2Mo': [], 'Oo2Mv': [] }
  for resource in pkg.resources:
    ldType = resource.descriptor['description']
    converters = {}
    dfs[ldType] = pd.DataFrame(
      resource.read(),
      columns=resource.headers,
    )
    for field in resource.descriptor['schema']['fields']:
      if field['type'] == 'string':
        dfs[ldType][field['name']] = dfs[ldType][field['name']].astype('str')
      elif field['type'] == 'integer':
        dfs[ldType][field['name']] = dfs[ldType][field['name']].astype('int64')
      elif field['type'] == 'number':
        dfs[ldType][field['name']] = dfs[ldType][field['name']].astype('float64')
      elif field['type'] == 'boolean':
        dfs[ldType][field['name']] = dfs[ldType][field['name']].astype('bool')
    #
    if '@id' in resource.headers:
      dfs[ldType] = dfs[ldType].set_index('@id')
    if len(resource.descriptor['schema']['primaryKey']) == 2 and len(resource.descriptor['schema'].get('foreignKeys', [])) == 2:
      left_field, right_field = resource.descriptor['schema']['primaryKey']
      left_rel, right_rel = resource.descriptor['schema']['foreignKeys']
      rels['Mo2Mo'].append(dict(
        through=ldType,
        through_subject=left_field,
        through_object=right_field,
        subject=left_rel['reference']['resource'],
        predicate=right_field.split('_')[0],
        object=right_rel['reference']['resource'],
      ))
    if len(resource.descriptor['schema']['primaryKey']) == 2 and len(resource.descriptor['schema'].get('foreignKeys', [])) == 1:
      left_field, right_field = resource.descriptor['schema']['primaryKey']
      left_rel, = resource.descriptor['schema']['foreignKeys']
      rels['Oo2Mv'].append(dict(
        through=ldType,
        through_subject=left_field,
        through_object=right_field,
        subject=left_rel['reference']['resource'],
        predicate=right_field.split('_')[0],
      ))
    else:
      for rel in resource.descriptor['schema'].get('foreignKeys', []):
        rels['Oo2Mo'].append(dict(
          subject=ldType,
          predicate=rel['fields'],
          object=rel['reference']['resource'],
        ))
  #
  return pandas.from_dfs(dfs, rels)
