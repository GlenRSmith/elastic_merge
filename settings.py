"""
Provide settings with default values
Allow environment overrides
"""

from os import environ
try:
    ES_HOST = environ["ES_HOST"]
except:
    ES_HOST = "http://localhost:9200"

INDEX = "elastic_merge"
