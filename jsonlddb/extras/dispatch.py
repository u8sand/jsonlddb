from jsonlddb import JsonLDDatabase
from jsonlddb.extras import rules

class JsonLDDispatch:
  def __init__(self):
    self._context = {}
    self._rules = JsonLDDatabase()

  def register(self, given={}, produce={}):
    def wrapper(func):
      self._rules.insert({
        '@type': 'Rule',
        'given': given,
        'produce': produce,
        'using': func.__name__,
      })
      self._context[func.__name__] = func
      return func
    return wrapper
  
  def frame(self, db, frame):
    return rules.frame_with_rules(db, frame, rules=self._rules, context=self._context)
