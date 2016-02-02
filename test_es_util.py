#!/usr/bin/env python
# -*- coding: utf8 -*-
import inspect
from os import path
import sys
import unittest2
import xmlrunner

from es_util import create_index, delete_index, flush_index, index_doc, search
from gen_utils import read_json_file

CWD = path.dirname(__file__)
DATA_DIR = path.join(CWD, "test_data")
TEST_HOST = "http://localhost:9200"
INDEX = "elastic_merge"


def read_doc_file(filename):
    return read_json_file(path.join(DATA_DIR, filename))


class TestSearch(unittest2.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            delete_index(TEST_HOST, INDEX)
        except Exception as err:
            print(u'err: {0}, no1curr'.format(err))
        index_config = read_doc_file("index.json")
        create_index(TEST_HOST, INDEX, index_config)
        # in Elasticsearch, parents don't know about children,
        # so we index the test docs from the 'top down':
        TestSearch.twitter1 = read_doc_file("twitter1.json")
        TestSearch.twitter1_id = index_doc(
            TEST_HOST, INDEX, 'twitter', TestSearch.twitter1)
        TestSearch.tweet1 = read_doc_file("tweet1.json")
        TestSearch.tweet1_id = index_doc(
            TEST_HOST, INDEX, 'tweet', TestSearch.tweet1,
            parent_id=TestSearch.twitter1_id)
        TestSearch.tweet2 = read_doc_file("tweet2.json")
        TestSearch.tweet2_id = index_doc(
            TEST_HOST, INDEX, 'tweet', TestSearch.tweet2,
            parent_id=TestSearch.twitter1_id)
        TestSearch.loc1 = read_doc_file("location1.json")
        TestSearch.loc1_id = index_doc(
            TEST_HOST, INDEX, 'location', TestSearch.loc1,
            parent_id=TestSearch.tweet1_id)
        TestSearch.loc2 = read_doc_file("location2.json")
        TestSearch.loc2_id = index_doc(
            TEST_HOST, INDEX, 'location', TestSearch.loc2,
            parent_id=TestSearch.tweet2_id)
        flush_index(TEST_HOST, INDEX)


    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.twitter_crit = {"match": {"condition": "sleepy"}}
        self.tweet_crit = {"match": {"status": "Recruiting"}}
        self.loc_crit = {"match": {"address.city": "Chicago"}}
        self.twitter_parent_crit = {
            "has_parent": {
                "type": "twitter",
                "query": self.twitter_crit}}
        self.tweet_child_crit = {
            "has_child": {
                "type": "tweet",
                "query": self.tweet_crit}}
        return

    def tearDown(self):
        return

    def test_01_indexed(self):
        # quick verification that the indexing succeeded
        self.assertEqual(TestSearch.twitter1_id, 'twitter.x009A02')
        self.assertEqual(TestSearch.tweet1_id, 'tweet.x00000001')
        self.assertEqual(TestSearch.tweet2_id, 'tweet.x00000005')
        self.assertEqual(TestSearch.loc1_id, 'location.x0000030A')
        self.assertEqual(TestSearch.loc2_id, 'location.x00001034')
        return

    def test_twitter_search(self):
        # Find a twitter by tweet criteria
        search1 = self.tweet_child_crit
        twitters = search(TEST_HOST, INDEX, 'twitter', search1)
        self.assertEqual(twitters[0], TestSearch.twitter1)
        return

    def test_tweet_search(self):
        # Find tweets by twitter criteria
        search2 = self.twitter_parent_crit
        tweets = search(TEST_HOST, INDEX, 'tweet', search2)
        self.assertIn(TestSearch.tweet1, tweets)
        self.assertIn(TestSearch.tweet2, tweets)
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
