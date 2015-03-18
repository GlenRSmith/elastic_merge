#!/usr/bin/env python
# -*- coding: utf8 -*-
import copy
import inspect
import json
from os import path
import sys
import unittest2
import xmlrunner

from es_util import create_index, delete_index, flush_index, index_doc
from es_wrap import search_merge, post_graph_search
from gen_utils import read_json_file

CWD = path.dirname(__file__)
DATA_DIR = path.join(CWD, "test_data")
INDEX = "elastic_merge"


def read_doc_file(filename):
    return read_json_file(path.join(DATA_DIR, filename))


class TestSearchMerge(unittest2.TestCase):

    @classmethod
    def setUpClass(cls):
        try:
            delete_index(INDEX)
        except Exception as err:
            print(u'err: {0}, no1curr'.format(err))
        index_config = read_doc_file("index.json")
        create_index(INDEX, index_config)
        # in Elasticsearch, parents don't know about children,
        # so we index the test docs from the 'top down':
        TestSearchMerge.twitter1 = read_doc_file("twitter1.json")
        TestSearchMerge.twitter1_id = index_doc(
            INDEX, 'twitter', TestSearchMerge.twitter1)
        TestSearchMerge.tweet1 = read_doc_file("tweet1.json")
        TestSearchMerge.tweet1_id = index_doc(
            INDEX, 'tweet', TestSearchMerge.tweet1,
            parent_id=TestSearchMerge.twitter1_id)
        TestSearchMerge.tweet2 = read_doc_file("tweet2.json")
        TestSearchMerge.tweet2_id = index_doc(
            INDEX, 'tweet', TestSearchMerge.tweet2,
            parent_id=TestSearchMerge.twitter1_id)
        TestSearchMerge.loc1 = read_doc_file("location1.json")
        TestSearchMerge.loc1_id = index_doc(
            INDEX, 'location', TestSearchMerge.loc1,
            parent_id=TestSearchMerge.tweet1_id)
        TestSearchMerge.loc2 = read_doc_file("location2.json")
        TestSearchMerge.loc2_id = index_doc(
            INDEX, 'location', TestSearchMerge.loc2,
            parent_id=TestSearchMerge.tweet2_id)
        flush_index(INDEX)


    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.twitter_crit = {"match": {"condition": "sleepy"}}
        self.tweet_crit = {"match": {"status": "Recruiting"}}
        self.loc_crit = {"match": {"address.city": "Chicago"}}
        self.twitter_parent_crit = {
            "has_parent": {"type": "twitter", "query": self.twitter_crit}}
        self.tweet_child_crit = {
            "has_child": {"type": "tweet", "query": self.tweet_crit}}
        self.expect_twitter_merge = copy.deepcopy(TestSearchMerge.twitter1)
        self.expect_twitter_merge['_merged'] = {}
        self.expect_twitter_merge['_merged']['tweet'] = {}
        self.expect_twitter_merge = TestSearchMerge.tweet1
        return

    def tearDown(self):
        return

    def test_01_indexed(self):
        # quick verification that the indexing succeeded
        self.assertEqual(TestSearchMerge.twitter1_id, 'twitter.x009A02')
        self.assertEqual(TestSearchMerge.tweet1_id, 'tweet.x00000001')
        self.assertEqual(TestSearchMerge.tweet2_id, 'tweet.x00000005')
        self.assertEqual(TestSearchMerge.loc1_id, 'location.x0000030A')
        self.assertEqual(TestSearchMerge.loc2_id, 'location.x00001034')
        return

    def test_search_merge_twitters(self):
        twitters = search_merge('twitter', self.twitter_crit, 'tweet', self.tweet_crit)
        self.assertEqual(len(twitters), 1)
        for tag in ['_merged', 'condition', 'intervention', 'id_info']:
            self.assertIn(tag, twitters[0])
        self.assertIn('tweet', twitters[0]['_merged'])
        self.assertEqual(
            twitters[0]['_merged']['tweet'][0], TestSearchMerge.tweet1)
        self.assertEqual(
            twitters[0]['_links']['self']['href'], TestSearchMerge.twitter1_id)
        return

    def test_search_merge_tweets(self):
        tweets = search_merge('tweet', self.tweet_crit, 'twitter', self.twitter_crit)
        self.assertEqual(len(tweets), 1)
        for tag in ['_merged', 'status', '_links']:
            self.assertIn(tag, tweets[0])
        self.assertIn('twitter', tweets[0]['_merged'])
        self.assertDictEqual(
            tweets[0]['_merged']['twitter'][0], TestSearchMerge.twitter1)
        self.assertEqual(
            tweets[0]['_links']['self']['href'], TestSearchMerge.tweet1_id)
        return

    def test_get_tweet_graph(self):
        rel_args = {'twitter': self.twitter_crit, 'location': self.loc_crit}
        # tweets = get_document_graph('tweet', self.tweet_crit, rel_args)
        tweets = post_graph_search({
            "query": {
                "doc_type": "tweet",
                "doc_criteria": self.tweet_crit,
                "rel_criteria": rel_args
            }
        })
        self.assertEqual(len(tweets), 1)
        for tag in ['_merged', 'status', '_links']:
            self.assertIn(tag, tweets[0])
        self.assertEqual(
            tweets[0]['_links']['self']['href'], TestSearchMerge.tweet1_id)
        self.assertIn('twitter', tweets[0]['_merged'])
        self.assertDictEqual(
            tweets[0]['_merged']['twitter'][0], TestSearchMerge.twitter1)
        self.assertIn('location', tweets[0]['_merged'])
        self.assertDictEqual(
            tweets[0]['_merged']['location'][0], TestSearchMerge.loc1)
        return


if __name__ == '__main__':
    args = sys.argv[1:]
    if len(args) == 0:
        # Run all tests here
        unittest2.main(testRunner=xmlrunner.XMLTestRunner(output='reports'))
    else:
        module_name = inspect.getmodulename(__file__)
        # Create a test suite with the args to run
        args = ['%s.%s' % (module_name, arg) for arg in args]
        suite = unittest2.TestLoader().loadTestsFromNames(args)
        unittest2.TextTestRunner(verbosity=2).run(suite)
