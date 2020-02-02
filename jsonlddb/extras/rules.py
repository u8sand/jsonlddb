from jsonlddb.oop import JsonLDDatabase

def frame_intersection(frame0, frame1):
  return (frame0.keys() & frame1.keys()) and all(
    frame0[k] == frame1[k] or frame0[k] == {} or frame1[k] == {}
    for k in (frame0.keys() & frame1.keys())
  )

def frame_with_rules(db, frame, rules=None, context={}):
  if rules is None:
    rules = db
  # Apply rule IFF
  #  1) desired frame overlaps with produce frame
  #  2) given frame can be satisfied by query
  tmp = JsonLDDatabase()
  # Consider all rules
  for rule in rules[{'@type': 'Rule'}]:
    # such that desired frame overlaps with produce frame
    if frame_intersection(frame, rule['produce'][0]):
      # and given frame satisfies query
      for matching_doc in db[rule['given'][0]]:
        # Add rule-created triples
        tmp.insert(context[rule['using'][0]](matching_doc))
  # Frame injecting tmp values
  return db.with_db(tmp)[frame]
