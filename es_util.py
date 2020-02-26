#!/usr/bin/env python
# -*- coding:utf-8 -*-
import json
from os import path

import requests
from settings import ES_HOST as HOST
from settings import INDEX

# (unguarded) singleton for lazy init
MAPPINGS = None


def delete_index(host, index_name):
    index_res = requests.delete(path.join(host, index_name))
    if not index_res.status_code == 200:
        err = u'index_res: {0} - {1}'.format(index_res, index_res.text)
        raise Exception(err)
    return index_res


def create_index(host, index_name, config):
    """
    Create an ES index with the (json) configuration
    """
    index_res = requests.post(path.join(host, index_name),
                              data=json.dumps(config))
    if not index_res.status_code == 200:
        err = u'index_res: {0} - {1}'.format(index_res, index_res.text)
        raise Exception(err)
    return


def flush_index(host, index_name):
    return requests.post(path.join(host, index_name, '_flush'))


def get_mappings(host):
    global MAPPINGS
    if not MAPPINGS:
        maps_url = path.join(host, INDEX, '_mapping')
        res = requests.get(maps_url)
        MAPPINGS = res.json()[INDEX]["mappings"]
    return MAPPINGS


def get_id_path(host, doc_type):
    return get_mappings(host)[doc_type]["_id"]["path"]


def get_doc_id(host, doc, doc_type):
    ptr = doc
    for tag in get_id_path(host, doc_type).split('.'):
        ptr = ptr[tag]
    return ptr


def index_doc(host, index_name, type_name, doc, parent_id=None):
    """
    indexes the document into the named index and type_name
    returns the ES assigned _id
    """
    index_url = path.join(host, index_name, type_name)
    params = {}
    if parent_id:
        params['parent'] = parent_id
    if type(doc) is dict:
        doc = json.dumps(doc)
    index_res = requests.post(index_url, data=doc, params=params)
    if not index_res.status_code == 201:
        msg = u'index_url: {0}\n'.format(index_url)
        msg += u'doc: {0}\n'.format(doc)
        msg += u'index_res: {0} - {1}\n'.format(index_res, index_res.text)
        print(msg)
        raise Exception(msg)
    return index_res.json()['_id']


def search(host, index_name, type_name, crit):
    def build_bool_list(criteria, must=None):
        """
        recursive function to build a must, should, or must_not list in a bool
        """
        if must is None:
            must = []
        if type(criteria) is dict:
            must.append(criteria)
        elif type(criteria) is list:
            for criterion in criteria:
                build_bool_list(criterion, must)
        else:
            raise Exception(u'criteria {0} not list or dict'.format(criteria))
        return must

    search_url = path.join(host, index_name, type_name, '_search') + '?pretty'
    # print(u'search_url: {0}'.format(search_url))
    # print(u'crit: {0}'.format(crit))
    query = {"query": {"bool": {"must": build_bool_list(crit)}}}
    # print(u'query: {0}'.format(query))
    # print(u'query: {0}'.format(json.dumps(query, indent=2)))
    res = requests.post(search_url, data=json.dumps(query))
    if res.status_code != 200:
        print(u'query: {0}'.format(json.dumps(query, indent=2)))
        raise Exception(u'search failure: {0}'.format(res.text))
    docs = map(
        lambda _ref: _ref['_source'],
        res.json()['hits']['hits'])
    # print(u'docs: {0}'.format(json.dumps(docs, indent=2)))
    return docs
