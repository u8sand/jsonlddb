'''
This Json LD Database and other convenient classes should prove very
 useful with loading in JsonLD and actually using it. It identifies
 nodes that are the same and ensures they are treated the same. It
 exposes a mechanism of access resembling a large set of json objects
 while saving duplication only once and enabling circular referencing.

It is quite computationally efficient using hashtables and sets to
 quickly narrow down and satisfy frames (at the cost of a good amount of
 nested hash tables -- $2*(S*(2*P)*O)$ literals). For many operations
 including Json LD Framing this results in query satisfaction bound only
 by the (deep) size of your frame (likely quite small).

While perhaps space-prohibitive for large amounts of data, for small to
 mid-ranged amounts of data like what I anticipate to use this for
 (Json-LD Dispatch), this approach will have no extensive negative
 performance impacts.

It works somewhat intuitively--allowing you to access the database as you
 might a json object--using frames for selection.

Important assumptions made by this architecture:
  - Unless an @id is specified, literals--not connections--are
    used to distinguish any given node.
  - In the case that an @id is specified with different literals,
    those literals will be merged into a single object.
  - Strong Json-LD Structure is enforced (i.e. values are lists)
    ({ '@id': subj, 'pred': [{...}], ... })

'''

from .jsonld_oop import JsonLDDatabase, JsonLDFrame, JsonLDNode
