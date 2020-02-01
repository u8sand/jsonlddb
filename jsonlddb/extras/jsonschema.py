import re
from jsonlddb.core import utils, json

def to_jsonschema(db, additionalProperties=False):
  schema = {
    'components': {
      'Json': {
        'oneOf': [
          { 'type': 'string' },
          { 'type': 'number' },
          { 'type': 'boolean' },
          { 'type': 'array',
            'items': {
              '$ref': '#/components/Json'
            } },
          { 'type': 'object',
            'additionalProperties': {
              'keyType': 'string',
              'valueType': {
                '$ref': '#/components/Json'
              }
            } }
        ]
      },
      'JsonLD': {
        'allOf': [
          { '$ref': '#/components/Json' },
          { 'oneOf': [
            { 'type': 'object',
              'properties': {
                '@id': {
                  'type': 'string'
                },
                '@type': {
                  'type': 'string'
                }
              },
              'additionalProperties': {
                '^.*$': {
                  'keyType': 'string',
                  'valueType': {
                    'oneOf': [
                      { '$ref': '#/components/JsonLD' },
                      { '$ref': '#/components/Json' },
                    ]
                  }
                }
              } },
          { 'type': 'array',
            'items': {
              '$ref': '#/components/JsonLD'
            } }
          ] }
        ]
      }
    }
  }
  preds = {
    p
    for p, os in db.index.pos.items()
    if not re.match(r'^[~@]', p)
  }
  for ldType in db['@type']:
    ldTypeSchema = {
      'type': 'object',
      'properties': {
        '@id': {
          'type': 'string',
        },
        '@type': {
          'type': 'string',
          'enum': [ldType],
        },
      },
      'patternProperties': {
        '^.*$': {
          'keyType': 'string',
          'valueType': '#/components/Json',
        },
      },
      'additionalProperties': additionalProperties,
      'required': [],
    }
    for pred in preds:
      pyTypes = {(utils.isLiteral(v), type(v)) for v in db[{'@type': ldType}][pred]}
      predProps = {'anyOf': set()}
      n_pyTypes = len(pyTypes - {(False, type(None)), (True, type(None))})
      if n_pyTypes == 0:
        continue
      elif n_pyTypes == 1:
        isLiteral, pyType = next(iter(pyTypes))
        if isLiteral:
          if pyType == str:
            predProps['anyOf'].add(json.JSON({'type': 'string'}))
            predProps['anyOf'].add(json.JSON({'type': 'array', 'item': 'string'}))
          elif pyType == bool:
            predProps['anyOf'].add(json.JSON({'type': 'boolean'}))
            predProps['anyOf'].add(json.JSON({'type': 'array', 'item': 'boolean'}))
          elif pyType == int or pyType == float:
            predProps['anyOf'].add(json.JSON({'type': 'number'}))
            predProps['anyOf'].add(json.JSON({'type': 'array', 'item': 'number'}))
          else:
            predProps['anyOf'].add(json.JSON({'$ref': '#/components/Json'}))
        else:
          predProps['anyOf'].add(json.JSON({
            '$ref': '#/components/JsonLD',
          }))
          objs = db[{'@type': ldType}]
          fLdTypes = set(objs[pred]['@type'])
          for fLdType in fLdTypes:
            if any(len(record[pred][{'@type': fLdType}]) > 1 for record in objs):
              # m2m
              predProps['anyOf'].add(json.JSON({
                'type': 'array',
                'items': {
                  '$ref': '#/components/' + fLdType,
                }
              }))
            else:
              predProps['anyOf'].add(json.JSON({
                '$ref': '#/components/JsonLD',
              }))
              predProps['anyOf'].add(json.JSON({
                '$ref': '#/components/' + fLdType,
              }))
          #
        #
      else:
        predProps['anyOf'].add(json.JSON({
          '$ref': '#/components/JsonLD',
        }))
      #
      if len(predProps['anyOf']) == 0:
        continue
      elif len(predProps['anyOf']) == 1:
        predProps = dict(predProps['anyOf'][0])
      else:
        predProps['anyOf'] = [dict(prop) for prop in predProps['anyOf']]
      #
      ldTypeSchema['properties'][pred] = predProps
      if {(False, type(None)), (True, type(None))} & pyTypes:
        ldTypeSchema['required'].append(pred)
    if not ldTypeSchema['required']:
      del ldTypeSchema['required']
    #
    schema['components'][ldType] = ldTypeSchema
  #
  return schema
