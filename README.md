Purpose:

Models one option for a ReSTful endpoint which would support searching for and returning related documents

Next steps:

Write a flask service to wrap the imitation ReST methods 

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
      
