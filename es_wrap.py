#!/usr/bin/env python
# -*- coding:utf-8 -*-
# import json

from es_util import get_doc_id, get_id_path, get_mappings, search

INDEX = "elastic_merge"
MAPPINGS = None


class ElasticWrapHelper(object):
    """
    Helper class - only to be used by NewElasticEndpoint
    (makes that class easier to read)
    """

    def __init__(self, host):
        self.host = host

    def has_nested(self, source_type, target_type):
        """
        returns whether the source_type has target_type as a nested property
        """
        mapping = get_mappings(self.host)
        try:
            tt = mapping[source_type]["properties"][target_type]["type"]
            return tt == "nested"
        except:
            return False

    def has_ref(self, source_type, target_type):
        """
        returns whether the source_type has a ref to the target_type
        in the current implementation it's in the form of a parent
        """
        mapping = get_mappings(self.host)
        if source_type not in mapping:
            raise Exception(u'unknown type {0}'.format(source_type))
        if target_type not in mapping:
            raise Exception(u'unknown type {0}'.format(target_type))
        if '_parent' not in mapping[source_type]:
            # print(u'mapping[source_type].keys(): {0}'.format(
            # mapping[source_type].keys()))
            return False
        return mapping[source_type]['_parent']['type'] == target_type

    def get_rel_type(self, doc_type, merge_type):
        """
        returns name for relationship from doc_type to merge_type
        'doc_type has_parent/has_child merge_type'
        :param doc_type:
        :param merge_type:
        :return:
        """
        if self.has_ref(doc_type, merge_type):
            # doc_type definition has the merge_type as its _parent property
            rel = "has_parent"
        elif self.has_ref(merge_type, doc_type):
            # merge_type definition has the doc_type as its _parent property
            rel = "has_child"
        elif self.has_nested(doc_type, merge_type):
            rel = "_has_nested"
        elif self.has_nested(merge_type, doc_type):
            rel = "is_nested"
        else:
            raise Exception(u'{0} & {1} have no mapped relationship'.format(
                doc_type, merge_type))
        return rel

    def find_ref_docs(self, doc, doc_type, find_type, find_criteria):
        """
        :param doc: find documents related to this one, as indexed
        :param doc_type: indexed type of doc required to be related
        :param find_type: indexed type being searched
        :param find_criteria: search criteria for find_type docs
        :return: list of docs of find_type, related to doc, matching find_criteria
        """
        rel = self.get_rel_type(find_type, doc_type)
        doc_id_path = get_id_path(self.host, doc_type)
        if '_merged' not in doc:
            doc['_merged'] = {find_type: []}
        if find_type not in doc['_merged']:
            doc['_merged'][find_type] = []
        doc_id_crit = {
            "term": {doc_id_path: get_doc_id(self.host, doc, doc_type)}}
        return search(
            self.host,
            INDEX, find_type,
            [find_criteria, {rel: {"type": doc_type, "query": doc_id_crit}}])


class NewElasticEndpoint(object):
    def __init__(self, host):
        self.host = host
        self.helper = ElasticWrapHelper(host)
        return

    def find_and_merge(self, doc, doc_type, merge_type, merge_criteria):
        """
        find docs of merge_type that are connected to doc and meet merge_criteria,
        and merge them into doc
        :param doc: document into which the merge will be done
        :param doc_type: indexed type of document doc
        :param merge_type: document types to be searched and merged
        :param merge_criteria:
        :return:
        """
        ref_hits = self.helper.find_ref_docs(
            doc, doc_type, merge_type, merge_criteria)
        for ref_hit in ref_hits:
            doc['_merged'][merge_type].append(ref_hit)
        return doc

    def get_document_graph(self, doc_type, doc_criteria, rel_criteria):
        """
        Each of the doc_criteria may contain additional rel_criteria
        :param doc_type:main doc_type to search and return
        :param doc_criteria:search criteria for main doc_type
        :param rel_criteria:dict of rel_type:doc_criteria for rel_type
        :return:a single json document with referenced documents resolved
        """
        # ES only supports a parent/child relationship & a nested relationship
        # The mapping of the child document specifies a property named "_parent"
        # I'm trying to abstract that detail to support a possible eventual
        # change to a more general reference model, without knowledge of
        # how the document connections might be represented in that design.
        crit_list = [doc_criteria]
        for other_type in rel_criteria:
            other_criteria = rel_criteria[other_type]
            rel_type = self.helper.get_rel_type(doc_type, other_type)
            crit_list.append(
                {rel_type: {"type": other_type, "query": other_criteria}})
        docs = search(self.host, INDEX, doc_type, crit_list)
        for other_type in rel_criteria:
            other_criteria = rel_criteria[other_type]
            for doc in docs:
                self.find_and_merge(doc, doc_type, other_type, other_criteria)
        # print(u'merged docs: {0}'.format(json.dumps(docs, indent=2)))
        return docs


def post_graph_search(host, query):
    """
    json endpoint for get_document_graph
    :param query:
    :return:
    """
    search_body = query["query"]
    for lbl in ["doc_type", "doc_criteria", "rel_criteria"]:
        if lbl not in search_body:
            raise Exception(u'{0} is missing'.format(lbl))
    # print(json.dumps(query, indent=2))
    endpoint = NewElasticEndpoint(host)
    ret_val = endpoint.get_document_graph(
        search_body["doc_type"],
        search_body["doc_criteria"],
        search_body["rel_criteria"])
    return ret_val
