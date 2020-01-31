import random

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

def random_jsonld(n_records, mu_rels, std_rels, mu_lits, std_lits, n_types):
  record_types = [
    random_string()
    for _ in range(n_types)
  ]
  pred_types = {
    random_string(): random.choice([
      random_string,
      lambda: random.randint(0, 100),
      lambda: random.random(),
      lambda: random.choice([True, False]),
      lambda: None,
    ])
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
      record[pred].append(pred_types[pred]())
    for _ in range(n_rels):
      pred = random.choice(rel_types)
      if record.get(pred) is None:
        record[pred] = []
      record[pred].append({
        '@id': str(random.randint(0, n_records))
      })
    yield record
