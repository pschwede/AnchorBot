#!/usr/bin/env python
# -*- encoding: utf-8 -*-

"""
This is the main class of AnchorBot, the feed reader that makes you read
the important news first.

For further reading, see README.md
"""

import feedparser
import sys
import os
import urllib
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql.expression import desc

import storage
from logger import Logger
from config import Config
from crawler import Crawler
from datamodel import (get_session,
                                get_engine, Source, Article, Image, Keyword)
from analyzer import Analyzer

from processor import Processor
from multiprocessing import Lock

from time import time, sleep

HOME = os.path.join(os.path.expanduser("~"), ".anchorbot")
HERE = os.path.realpath(os.path.dirname(__file__))
TEMP = os.path.join(HOME, "cache/")
HTML = os.path.join(HOME, "index.html")
NUMT = 1 #FIXME reduced due to database conflicts
__appname__ = "AnchorBot"
__version__ = "1.1"
__author__ = "spazzpp2"

class Anchorbot(object):
    """ The most main Class

    It holds and calls initialization of:
    * singleton instance lock
    * configurations
    * feed downloads
    * start analysis of the downloaded feeds
    """

    def __init__(self, verbose=False, cache_only=False, update_call=lambda x:x):
        self.verbose = verbose
        l = Logger(verbose, write=os.path.join(HOME, "logger.log"))
        self.log = l.log

        # prepare lock, config, cache and variables
        try:
            # load config
            try:
                # Raises Exception if locked
                self.config = Config(HOME, verbose=self.verbose)
            except Exception, e:
                print str(e)
                sys.exit(1)


            # cache keeps files for 3 days
            self.cache = storage.FileCacher(TEMP, 3 , False)

            # prepare datamodel
            path = os.path.join(HOME, "database.sqlite")
            self.db = get_engine(path)

            # prepare variables and lists,...
            self.feeds = {}
            self.watched = None
            self.analyzer = Analyzer(key="title", eid="link")
            self.crawler = Crawler(self.cache, self.analyzer)
            self.crawler.verbose = self.verbose
            self.dblock = Lock()
            # start daemons that can download
            self.downloader = Processor(NUMT, self.download, update_call)
            # in background, make daemons download feeds
            #TODO load from config
            self.running, self.timeout = True, 3000
            self.downloader.run_threaded(self.update_all, update_call)
        except IOError:
            sys.exit(1)

        # print out cache and exit
        if cache_only:
            self.__print_cache_and_exit()

    def __print_cache_and_exit(self):
        """ well, prints cache and exits """
        self.downloader.running = False
        # print
        self.cache.pprint()
        # shutdown
        self.cache.shutdown()
        self.config.shutdown()
        sys.exit(0)

    def shutdown(self, stuff=None):
        """Does a save shutdown"""
        # stop downloading
        self.running = False
        self.downloader.running = False
        # shutdown
        self.cache.shutdown()
        self.config.shutdown()
        sys.exit(0)

    def enrich(self, entries, source):
        for entry in entries:
            url = self.crawler.get_link(entry)
            s = get_session(self.db)
            article = s.query(Article).filter(Article.link == url).count()
            s.close()
            if article == 0:
                s = get_session(self.db)
                article, keywords = self.crawler.enrich(entry, source)
                if keywords:
                    article.set_keywords([(s.query(Keyword).filter(Keyword.word == kw.word).first() or kw) for kw in keywords])
                try:
                    s.add(article)
                    s.commit()
                except IntegrityError:
                    s.rollback()
                    if article.image and article.image in s:
                        s.expunge(article.image)
                    article.image = s.query(Image).filter(Image.filename == article.image.filename).first()
                    try:
                        s.add(article)
                        s.commit()
                    except IntegrityError:
                        s.rollback()
                        if article.image and article.image in s:
                            s.expunge(article.image)
                        article.image = None
                        s.add(article)
                        s.commit()
            s.close()

    def download(self, feedurl, callback=None):
        """Download procedure"""
        del self.cache[feedurl] # make sure, you got the newest
        feed = self.feeds[feedurl] = feedparser.parse(self.cache[feedurl])
        s = get_session(self.db)
        source = s.query(Source).filter(Source.link == feedurl).first()
        try:
            title = source.title = feed["feed"]["title"]
        except KeyError:
            title = source.title = feedurl
        s.close()

        # make DLer start some processes to enrich entries
        self.downloader.map(self.enrich, feed["entries"], source)

        self.log("Done %i of %i" % (self.feeds.keys().index(feedurl) + 1, len(self.feeds),))
        if callback:
            callback(feedurl, title)

    def get_hash(self, feedurl):
        """Fast value for comparisons without hashing"""
        del self.cache[feedurl]
        self.cache[feedurl]
        return hash(feedurl)

    def update_all(self, callback=None):
        """Puts all feeds into the download queue to be downloaded.
        Needs some DLers in downloaders list
        """
        while self.running:
            for url in self.config.get_abos():
                s = get_session(self.db)
                source = s.query(Source).filter(Source.link == url).first()
                if not source:
                    self.log("New source: %s" % url)
                    source = Source(url)
                    s.add(source)
                    try:
                        s.commit()
                    except IntegrityError:
                        s.rollback()
                        self.log("Couldn't store source %s" % source)

                h = self.get_hash(url)
                if not source.quickhash or h != source.quickhash:
                    self.log("Something new: %s" % url)
                    # throw url before the daemons
                    self.downloader.run_one(url)
                else:
                    if callback:
                        callback(source.link, source.title)
                    self.log("Nothing new: %s" % url)
                    s.close()
            sleep(self.timeout)

    def add_url(self, url):
        """Adds a feed url to the abos
        """
        self.config.add_abo(url)
        self.downloader.map(self.download, [url], self.update_feeds_tree)
        s = get_session(self.db)
        source = Source(url, None)
        s.add(source)
        s.commit()

    def remove_url(self, url):
        """Removes a feed url from the abos
        """
        self.config.del_abo(url)
        self.update_feeds_tree(url)

def get_cmd_options():
    usage = "anchorbot.py"
    return usage

if __name__ == "__main__":
    print "Please run anchorbot_server.py"
