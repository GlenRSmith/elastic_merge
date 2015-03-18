#!/usr/bin/env python
# -*- coding: utf8 -*-
import inspect
import sys
import unittest2
import xmlrunner

from api import get_link, get_self_link, set_link, link_doc


class TestGetLink(unittest2.TestCase):
    """
    Test class for get_link function
    """

    def setUp(self):
        self.twitter_link1 = "twitter.1"
        self.tweet_link1 = "tweet.1"
        self.tweet_link2 = "tweet.2"
        self.loc_link1 = "location.1"
        self.twitter = {
            "condition": "Chordoma",
            "_links": {
                "self": {"href": self.twitter_link1},
                "tweet": [
                    {"href": self.tweet_link1},
                    {"href": self.tweet_link2}
                ]
            }
        }
        self.tweet = {
            "status": "Enrolling",
            "_links": {
                "self": {"href": self.tweet_link1},
                "twitter": {"href": self.twitter_link1},
                "location": {"href": self.loc_link1}
            }
        }
        self.location = {
            "fn": "Billiards Cafe",
            "address": {"city": "Chicago"},
            "_links": {
                "self": {"href": self.loc_link1},
                "tweet": [{"href": self.tweet_link1}]
            }
        }
        return

    def tearDown(self):
        return

    def test_get_self(self):
        self.assertEqual(
            self.twitter_link1, get_link(self.twitter, 'twitter', 'self'))
        self.assertEqual(self.twitter_link1, get_self_link(self.twitter, 'twitter'))
        self.assertEqual(
            self.tweet_link1, get_link(self.tweet, 'tweet', 'self'))
        self.assertEqual(self.tweet_link1, get_self_link(self.tweet, 'tweet'))
        self.assertEqual(
            self.loc_link1, get_link(self.location, 'location', 'self'))
        self.assertEqual(
            self.loc_link1, get_self_link(self.location, 'location'))
        return

    def test_get_other(self):
        self.assertEqual(
            self.loc_link1, get_link(self.tweet, 'tweet', 'location'))
        return

    def test_get_others(self):
        actual = get_link(self.twitter, 'twitter', 'tweet')
        self.assertIn(self.tweet_link1, actual)
        self.assertIn(self.tweet_link2, actual)
        return


class TestSetLink(unittest2.TestCase):
    """
    Test class for set_link function
    """

    def setUp(self):
        self.twitter = {"condition": "Chordoma"}
        self.tweet = {"status": "Enrolling"}
        self.location = {
            "fn": "Billiards Cafe",
            "address": {"city": "Chicago"}}
        self.twitter_link1 = "twitter.1"
        self.twitter_link2 = "twitter.2"
        self.tweet_link1 = "tweet.1"
        self.tweet_link2 = "tweet.2"
        self.loc_link1 = "location.1"
        return

    def tearDown(self):
        return

    def test_link_twitter_tweets(self):
        set_link(self.twitter, 'twitter', 'tweet', self.tweet_link1)
        set_link(self.twitter, 'twitter', 'tweet', self.tweet_link2)
        self.assertIn('_links', self.twitter)
        self.assertIn('tweet', self.twitter['_links'])
        self.assertIn({'href': self.tweet_link1}, self.twitter['_links']['tweet'])
        self.assertIn({'href': self.tweet_link2}, self.twitter['_links']['tweet'])
        return

    def test_link_tweet_location(self):
        set_link(self.tweet, 'tweet', 'location', self.loc_link1)
        self.assertIn('_links', self.tweet)
        self.assertIn('location', self.tweet['_links'])
        self.assertEqual(
            self.loc_link1, self.tweet['_links']['location']['href'])
        return


class TestLinkDoc(unittest2.TestCase):
    def setUp(self):
        self.twitter_link1 = "twitter.1"
        self.tweet_link1 = "tweet.1"
        self.loc_link1 = "location.1"
        self.twitter = {
            "condition": "Chordoma",
            "_links": {
                "self": {"href": self.twitter_link1}
            }
        }
        self.tweet = {
            "status": "Enrolling",
            "_links": {
                "self": {"href": self.tweet_link1}
            }
        }
        self.location = {
            "fn": "Billiards Cafe",
            "address": {"city": "Chicago"},
            "_links": {
                "self": {"href": self.loc_link1}
            }
        }
        return

    def test_link_doc(self):
        link_doc(self.twitter, 'twitter', self.tweet, 'tweet', recip=True)
        set_link(self.twitter, 'twitter', 'tweet', self.tweet_link1)
        self.assertIn('tweet', self.twitter['_links'])
        self.assertIn('twitter', self.tweet['_links'])
        self.assertIn({'href': self.tweet_link1}, self.twitter['_links']['tweet'])
        self.assertIn({'href': self.twitter_link1}, self.tweet['_links']['twitter'])
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
