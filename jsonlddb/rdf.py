import enum
import functools

@functools.total_ordering
class RDFTermType(enum.Enum):
  IRI = 0
  LITERAL = 1
  #
  def __lt__(self, other):
    return hash(self) < hash(other)
  #
  def __hash__(self):
    if self == RDFTermType.IRI:
      return 0
    elif self == RDFTermType.LITERAL:
      return 1

@functools.total_ordering
class RDFTerm:
  def __init__(self, type=None, value=None):
    self.type = type
    self.value = value
  #
  def __eq__(self, other):
    return (self.type, hash(type(self.value)), self.value) == (other.type, hash(type(other.value)), other.value)
  #
  def __lt__(self, other):
    return (self.type, hash(type(self.value)), self.value) < (other.type, hash(type(other.value)), other.value)
  #
  def __hash__(self):
    return hash((self.type, self.value))
