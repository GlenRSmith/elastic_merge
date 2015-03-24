Purpose:

Models one option for a ReSTful endpoint which would support searching for and returning related documents

- api.py, test_api.py:
    - misleadingly named
    - handles the bits related to object digraph links

- es_util.py, test_es_util.py:
    - straight ES interactions; CrUD index & mappings, search
      
- es_wrap.py, test_es_wrap.py:
    - The purpose of this project
    - defines an API for searching for related documents and returning both 
    - provides an implementation that depends on, but encapsulates, multiple calls to ES as-is
    - send query to es_wrap.post_graph_search
      
Query form:
```
{
  "query": {
    "doc_type": "The type of document desired as the top-level returned",
    "doc_criteria": "search object for doc_type",
    "rel_criteria": {
      "a doc type 'related to' doc_type": "search object for this doc type",
      "another related doc type": "search object for this doc type"
    }
  }
}
```

Response form (extracted from the usual response with metadata and "hits"):
```
[
  {
    "field name(s) from matching doc_type": "field value(s)",
    "_merged": {
      "name of requested related doc_type": [
        {
          "field name(s) from matching related doc_type": "field value(s)"
        }
      ],
      "name of another requested related doc_type": [
        {
          "field name(s) from matching related doc_type": "field value(s)"
        }
      ]
    }
  },
  {
    
  }
]
```

 
Next steps:
 - Write a flask service to wrap the imitation ReST methods
 - refactor the response back into normal ES reply body, with metadata




Background:

I've spent quite a bit of time contemplating handling relationships, and questions around that
arise endlessly as RDB-experience developers begin to use ES to support their applications.
 
The cost of having ES support server-side resolution of related objects, and the
preferred ways of supporting such use cases is covered reasonably well here:
http://www.elastic.co/guide/en/elasticsearch/guide/current/relations.html

Nevertheless, I kept thinking about: if ES *did* support server-side "join" of related documents,
what would the DSL look like? What would the query format be, and how would the results be represented?

I took a direction from a RESTful API that I contributed to that included as a requested
representation "application/wds+json", where wds is "weak directed subgraph".

Once I had a fair idea of the query and result formats I liked, I had the idea of
creating a java plugin with its own url handler. Before I spent much time at that,
I decided that getting up to speed on the code base was an obstacle, and, hence,
decided to do this proof-of-concept in python.

I did realize before even publishing this PoC that the experimental "inner hits"
feature probably renders this whole project moot, but I want to make my attempt
publicly visible anyway.
 