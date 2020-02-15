import random
import functools

corpus = None

def random_string():
  global corpus
  if corpus is None:
    import nltk
    try:
      corpus = nltk.corpus.words.words()
    except LookupError:
      nltk.download('words')
      corpus = nltk.corpus.words.words()
  return random.choice(corpus)

def random_bool():
  return random.choice([True, False])

def random_float():
  return random.random()

def random_int(int_start=0, int_end=100):
  return random.randint(int_start, int_end)

def random_json_object(int_start=0, int_end=100, mu_attrs=3, std_attrs=2, max_depth=2):
  obj = {}
  n_attrs = min(int(random.gauss(mu_attrs, std_attrs)), 3 * std_attrs)
  for _ in range(n_attrs):
    obj[random_string()] = random_json(int_start=0, int_end=100, mu_attrs=mu_attrs, std_attrs=std_attrs, max_depth=max_depth - 1)
  return obj

def random_json(int_start=0, int_end=100, mu_attrs=3, std_attrs=2, max_depth=2):
  options = [
    random_int(int_start=int_start, int_end=int_end),
    random_string(),
    random_float(),
    random_bool(),
    None,
  ]
  if max_depth > 0:
    options.append(
      random_json_object(mu_attrs=mu_attrs, std_attrs=std_attrs, max_depth=max_depth),
    )
  return random.choice(options)

def random_json_factory(int_start=0, int_end=100, mu_attrs=3, std_attrs=2, max_depth=2):
  options = [
    functools.partial(random_int, int_start=int_start, int_end=int_end),
    random_string,
    random_float,
    random_bool,
    lambda: None,
  ]
  if max_depth > 0:
    options.append(
      functools.partial(random_json_object, mu_attrs=mu_attrs, std_attrs=std_attrs, max_depth=max_depth),
    )
  return random.choice(options)

def random_jsonld(n_records, mu_rels, std_rels, mu_lits, std_lits, n_types):
  record_types = [
    random_string()
    for _ in range(n_types)
  ]
  pred_types = {
    random_string(): random_json_factory()
    for _ in range(mu_lits + (3 * std_lits))
  }
  rel_types = [
    random_string()
    for _ in range(mu_rels + (3 * std_rels))
  ]
  for i in range(n_records):
    record = {
      '@id': str(i),
      '@type': random.choice(record_types),
    }
    n_lits = min(int(random.gauss(mu_lits, std_lits)), 3 * std_lits)
    n_rels = min(int(random.gauss(mu_rels, std_rels)), 3 * std_rels)
    for _ in range(n_lits):
      pred = random.choice(list(pred_types.keys()))
      if record.get(pred) is None:
        record[pred] = []
      obj = pred_types[pred]()
      if type(obj) == dict:
        record[pred].append({ '@value': obj })
      else:
        record[pred].append(obj)
    for _ in range(n_rels):
      pred = random.choice(rel_types)
      if record.get(pred) is None:
        record[pred] = []
      record[pred].append({
        '@id': str(random.randint(0, n_records))
      })
    yield record
