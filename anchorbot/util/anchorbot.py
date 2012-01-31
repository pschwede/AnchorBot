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
from sqlalchemy.exc import IntegrityError, DatabaseError
from sqlalchemy.sql.expression import desc

import storage
from logger import Logger
from config import Config
from crawler import Crawler
from datamodel import (get_session,
                                get_engine, Source, Article, Image, Keyword)
from time import time, sleep

HOME = os.path.join(os.path.expanduser("~"), ".anchorbot")
DBPATH = os.path.join(HOME, "database.sqlite")
HERE = os.path.realpath(os.path.dirname(__file__))
TEMP = os.path.join(HOME, "cache/")
HTML = os.path.join(HOME, "index.html")
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
        self.log = Logger(verbose, write=os.path.join(HOME, "logger.log")).log

        # print out cache and exit
        if cache_only:
            self.__print_cache_and_exit()

        try:
            # cache keeps files for 3 days
            self.cache = storage.FileCacher(TEMP, 3, verbose)

            # prepare datamodel
            self.db = get_engine(DBPATH)

            # prepare variables and lists,...
            self.feeds = {}
            self.watched = None
            self.crawler = Crawler(self.cache)
            self.crawler.verbose = self.verbose and False
            #TODO load from config
        except IOError, e:
            print "IOError !", e.filename

        # prepare lock, config, cache and variables
        # load config
        try:
            # Raises Exception if locked
            self.config = Config(HOME, verbose=verbose)
        except Exception, e:
            self.log(str(e))
            sys.exit(1)

        self.running, self.timeout = True, 3000
        self.update_all()

    def __print_cache_and_exit(self):
        """ well, prints cache and exits """
        # print
        self.cache.pprint()
        self.shutdown()

    def shutdown(self, stuff=None):
        """Does a save shutdown"""
        # stop downloading
        # shutdown
        self.cache.shutdown()
        self.config.shutdown()
        self.running = False

    def add_entry(self, entry, source):
        url = self.crawler.get_link(entry)

        s = get_session(self.db)
        try:
            if s.query(Article).filter(Article.link == url).count():
                s.close()
                return
        except DatabaseError:
            self.log("Database error: %s" % url)
            s.close()

        article, keywords, image_url = self.crawler.enrich(entry, source)
        s = get_session(self.db)
        s.add(article)
        s.commit()
        for kw in set(keywords):
            try:
                if s.query(Keyword).filter(Keyword.word == kw).count():
                    article.keywords.append(s.query(Keyword).filter(Keyword.word == kw).first())
                else:
                    article.keywords.append(Keyword(kw))
                s.merge(article)
                s.flush()
            except IntegrityError, e:
                s.rollback()
                self.log("Keyword '%s' ignored: %s" % (kw,e))
        if s.query(Image).filter(Image.filename == image_url).count():
            article.image = s.query(Image).filter(Image.filename == image_url).first()
        else:
            article.image = Image(image_url, self.cache[image_url])
        s.merge(article)
        s.commit()
        s.close()

    def download_feed(self, feedurl, i=0, callback=None):
        """Download procedure"""
        del self.cache[feedurl] # make sure, you get the newest
        feed = self.feeds[feedurl] = feedparser.parse(self.cache[feedurl])
        s = get_session(self.db)
        source = s.query(Source).filter(Source.link == feedurl).first()
        try:
            title = source.title = feed["feed"]["title"]
        except KeyError:
            title = source.title = feedurl
        old_quickhash = source.quickhash
        new_quickhash = self.get_quickhash(source.link)
        if old_quickhash != new_quickhash:
            source.quickhash = new_quickhash
            s.commit()
            s.close()
            for entry in feed["entries"]:
                self.add_entry(entry, source)
            self.log("Done %i of %i: %s" % (i,len(self.config.get_abos()),feedurl,))
        else:
            self.log("Nothing new in %i of %i: %s (%s == %s)" % (i,len(self.config.get_abos()),feedurl,old_quickhash,new_quickhash))
            s.close()

        #self.feeds[feedurl] = feedurl
        if callback:
            callback(feedurl, title)

    def get_quickhash(self, feedurl):
        """Fast value for comparisons without hashing"""
        while True:
            try:
                h = hash(open(self.cache[feedurl]).read())
                return h
            except:
                sleep(1)

    def update_all(self, callback=None):
        """Puts all feeds into the download queue to be downloaded.
        Needs some DLers in downloaders list
        """
        while self.running:
            urls = self.config.get_abos()
            self.cache.get_all(urls, delete=True)
            for i,url in zip(range(1, len(urls)+1),urls):
                s = get_session(self.db)
                source = s.query(Source).filter(Source.link == url).first()
                if not source:
                    self.log("New source: %s" % url)
                    source = Source(url)
                    s.add(source)
                    try:
                        s.flush()
                    except IntegrityError:
                        s.rollback()
                        self.log("Couldn't store source %s" % source)
                        continue
                s.commit()
                s.close()

                self.download_feed(url,i=i)
                callback and callback(source.link, source.title)
            last_time = time()
            while last_time > time() - self.timeout:
                sleep(3)

    def add_url(self, url):
        """Adds a feed url to the abos
        """
        self.config.add_abo(url)
        s = get_session(self.db)
        source = Source(url, None)
        s.add(source)
        s.commit()

    def remove_url(self, url):
        """Removes a feed url from the abos
        """
        self.config.del_abo(url)

def get_cmd_options():
    usage = "anchorbot.py"
    return usage

if __name__ == "__main__":
    print "Please run anchorbot_server.py"
