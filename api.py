#-*- coding:utf-8 -*-
"""
Functions related to an API, and how the various document entities relate
to each other, independent of any elasticsearch relationship scheme
"""
import gen_utils

# how do doc types link to each other
# TODO: allow functions to failover to "default"
LINK_MODEL = {
    "doc type": {
        "linked type": ""
    },
    "default": {
        "self": {
            "path": ["_links", "self"],
            "type": dict,
            "property": "href"
        }
    },
    "twitter": {
        "self": {
            "path": ["_links", "self"],
            "type": dict,
            "property": "href"
        },
        "tweet": {
            "path": ["_links", "tweet"],
            "type": list,
            "property": "href"
        }
    },
    "tweet": {
        "self": {
            "path": ["_links", "self"],
            "type": dict,
            "property": "href"
        },
        "twitter": {
            "path": ["_links", "twitter"],
            "type": list,
            "property": "href"
        },
        "location": {
            "path": ["_links", "location"],
            "type": dict,
            "property": "href"
        }
    },
    "location": {
        "self": {
            "path": ["_links", "self"],
            "type": dict,
            "property": "href"
        },
        "tweet": {
            "path": ["_links", "tweet"],
            "type": list,
            "property": "href"
        }
    }

}


def get_link(doc, doc_type, ref_name):
    """
    Returns a string representing the link(s) of the doc to a ref_name,
    link a twitter doc, 'twitter', 'tweet' returns a list
    """
    doc_link = doc
    ref_struct = LINK_MODEL[doc_type][ref_name]
    for step in ref_struct['path']:
        doc_link = doc_link[step]
    prop_name = ref_struct['property']
    if ref_struct['type'] == list:
        ret_val = map(lambda _ref: _ref[prop_name], doc_link)
    elif ref_struct['type'] == dict:
        ret_val = doc_link[prop_name]
    else:
        raise Exception(u'config error in {0}'.format(LINK_MODEL))
    return ret_val


def get_self_link(doc, doc_type):
    """
    Returns a string representing the link of the doc from
    the link it defines for itself
    """
    return get_link(doc, doc_type, 'self')


def set_link(doc, doc_type, target_type, target_link):
    # 'twitter' in LINK_MODEL
    assert(doc_type in LINK_MODEL)
    # 'tweet' in LINK_MODEL['twitter']
    assert(target_type in LINK_MODEL[doc_type])
    # twitter doc has a '_links' dict
    gen_utils.assure_in(doc, '_links', dict)
    # twitter doc['_links'] has a 'tweet' list
    # or tweet doc['_links'] has a 'location' dict
    targ_template = LINK_MODEL[doc_type][target_type]
    gen_utils.assure_in(doc['_links'], target_type, targ_template["type"])
    targ = doc
    for next in targ_template["path"]:
        targ = targ[next]
    targ_obj = {targ_template["property"]: target_link}
    if targ_template["type"] == dict:
        targ.update(targ_obj)
    elif targ_template["type"] == list:
        targ.append(targ_obj)
    return doc


def link_doc(doc, doc_type, target_doc, target_type, recip=False):
    targ_link = get_self_link(target_doc, target_type)
    set_link(doc, doc_type, target_type, targ_link)
    if recip:
        link_doc(target_doc, target_type, doc, doc_type)
    return
