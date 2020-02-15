import enum

class TermType(enum.Enum):
  IRI = 0
  LITERAL = 1
  #
  def __hash__(self):
    if self == TermType.IRI:
      return 0
    elif self == TermType.LITERAL:
      return 1
  #
  def __repr__(self):
    return 'IRI' if self == TermType.IRI else 'LITERAL'

class Term:
  def __init__(self, type=None, value=None):
    self.type = type
    self.value = value
  #
  def __eq__(self, other):
    return (self.type, hash(type(self.value)), self.value) == (other.type, hash(type(other.value)), other.value)
  #
  def __hash__(self):
    return hash((self.type, self.value))
  #
  def __repr__(self):
    return '{}:{}'.format(repr(self.type), repr(self.value))
