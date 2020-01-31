import re

def to_jsonschema(db):
  schema = {
    'components': {
      'Json': {
        'oneOf': [
          { 'type': 'string' },
          { 'type': 'number' },
          { 'type': 'boolean' },
          { 'type': 'array'
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
                      '$ref': '#/components/JsonLD',
                      '$ref': '#/components/Json',
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
      'additionalProperties': {
        '^.*$': {
          'keyType': 'string',
          'valueType': '#/components/Json',
        },
      },
      'required': [],
    }
    for pred in preds:
      pyTypes = {type(v) for v in db[{'@type': ldType}][pred]}
      if not pyTypes:
        continue
      predProps = {'oneOf': []}
      for pytype in (pyTypes - {type(None)}):
        if pytype == str:
          predProps['oneOf'].append({'type': 'string'})
        elif pytype == bool:
          predProps['oneOf'].append({'type': 'boolean'})
        elif pytype == int or pytype == float:
          predProps['oneOf'].append({'type': 'number'})
        else:
          predProps['oneOf'].append({'$ref': '#/components/JsonLD'})
      if len(predProps['oneOf']) == 0:
        continue
      elif len(predProps['oneOf']) == 1:
        predProps = predProps['oneOf'][0]
      ldTypeSchema['properties'][pred] = predProps
      if type(None) not in pyTypes:
        ldTypeSchema['required'].append(pred)
    if not ldTypeSchema['required']:
      del ldTypeSchema['required']
    #
    schema['components'][ldType] = ldTypeSchema
  #
  return schema
