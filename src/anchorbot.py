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
import cli.daemon
from sqlalchemy.exc import IntegrityError, DatabaseError

import storage
from logger import Logger
from config import Config
from crawler import Crawler
from datamodel import (
        get_session, get_engine, Source, Article, Image, Keyword, Media)
from time import sleep, time
import atexit

HOME = os.path.join(os.path.expanduser("~"), ".anchorbot")
DBPATH = os.path.join(HOME, "database.sqlite")
HERE = os.path.realpath(os.path.dirname(__file__))
TEMP = os.path.join(os.path.expanduser("~"), ".cache/anchorbot/")
HTML = os.path.join(HOME, "index.html")
__appname__ = "AnchorBot"
__version__ = "1.1"
__author__ = "spazzpp2"


class Anchorbot(object):
    """
    The most main class

    It holds and calls initialization of:
    * singleton instance lock
    * configurations
    * feed downloads
    * start analysis of the downloaded feeds
    """

    def __init__(self, verbose=False, cache_only=False,
            update_call=lambda x: x):
        self.verbose = verbose
        self.log = Logger(verbose, write=os.path.join(HOME, "logger.log")).log

        try:
            # cache keeps files for 3 days
            verbose and self.log("Init FileCacher dir=%s, days=%i, verbose=%s" % (TEMP, 3, verbose))
            self.cache = storage.FileCacher(TEMP, 3, verbose=verbose)

            # prepare datamodel
            verbose and self.log("Preparing database at %s" % DBPATH)
            self.db = get_engine(DBPATH)

            # prepare variables and lists,...
            verbose and self.log("Preparing variables and lists")
            self.watched = None

            verbose and self.log("Init crawler with cache")
            self.crawler = Crawler(self.cache)
            self.crawler.verbose = self.verbose

        except IOError, e:
            print "IOError !", e.filename

        # prepare lock, config, cache and variables
        # load config
        try:
            # Raises Exception if locked
            verbose and self.log("Loading config from %s" % HOME)
            self.config = Config(HOME, verbose=verbose)
        except Exception, e:
            self.log(str(e))
            sys.exit(1)

    def run(self):
        self.running, self.timeout = True, 30
        self.verbose and self.log("Running=%s, timeout=%i" % (self.running, self.timeout))
        try:
            timeout = self.timeout
            while self.running:
                t0 = time()
                somethings = self.update_all()
                if somethings:
                    timeout = max(0, self.timeout - time() + t0)
                else:
                    timeout = max(0, min(timeout * 2 - time() + t0, 4*60*60))
                self.verbose and self.log("sleeping %i s" % timeout)
                sleep(timeout)
        except KeyboardInterrupt:
            pass

    def __print_cache_and_exit(self):
        """ well, prints cache and exits """
        # print
        self.cache.pprint()
        self.shutdown()

    def shutdown(self, stuff=None):
        """Does a save shutdown"""
        # stop downloading
        # shutdown
        self.log("Shutting down...")
        self.running = False
        self.log("Shutting down cache")
        self.cache.shutdown()
        self.log("Shutting down config")
        self.config.shutdown()
        self.log("KTHXBYE!")

    def add_entry(self, entry, source):
        url = self.crawler.get_link(entry).encode("utf-8")

        s = get_session(self.db)
        try:
            if s.query(Article).filter(Article.link == url).count():
                s.close()
                return 0
        except DatabaseError:
            self.log("Database error: %s" % url)
            s.close()
            return 0

        article, keywords, image_url, media = self.crawler.\
                enrich(entry, source)
        s.add(article)
        s.commit()
        for kw in set(keywords):
            try:
                if s.query(Keyword).filter(Keyword.word == kw).count():
                    article.keywords.append(
                            s.query(Keyword).\
                                    filter(Keyword.word == kw).\
                                    first())
                else:
                    article.keywords.append(Keyword(kw))
                s.merge(article)
                s.flush()
            except IntegrityError, e:
                s.rollback()
                self.log("Keyword '%s' ignored: %s" % (kw, e))
        if s.query(Image).filter(Image.filename == image_url).count():
            article.image = s.query(Image).\
                    filter(Image.filename == image_url).\
                    first()
        else:
            article.image = Image(image_url, self.cache[image_url])
        if s.query(Media).filter(Media.filename == media).count():
            article.media = s.query(Media).\
                    filter(Media.filename == media).\
                    first()
        else:
            article.media = Media(media)
        s.merge(article)
        s.commit()
        s.close()
        return 1

    def download_feed(self, urls, callback=None):
        """Download procedure"""
        somethings = 0
        self.cache.get_all(urls, delete=True)
        sources = dict()
        hashes = dict()
        s = get_session(self.db)
        for source in set(s.query(Source).all()):
            sources[source.link] = source
            hashes[source.link] = source.quickhash
        s.close()
        for feedurl,i in zip(urls, range(len(urls))):
            try:
                old_quickhash = hashes[feedurl]
                new_quickhash = str(self.get_quickhash(feedurl))
                if old_quickhash == new_quickhash:
                    self.log("Nothing new in %i of %i: %s (%s == %s)" % (
                        i+1, len(urls),
                        feedurl, old_quickhash, new_quickhash))
                else:
                    self.log("Something new in %i of %i: %s (%s != %s)" % (
                        i+1, len(urls),
                        feedurl, old_quickhash, new_quickhash))
                    source = sources[feedurl]
                    source.quickhash = new_quickhash
                    feed = feedparser.parse(self.cache[feedurl])
                    try:
                        title = source.title = feed["feed"]["title"]
                    except KeyError:
                        title = source.title = feedurl
                    s = get_session(self.db)
                    s.merge(source)
                    s.commit()
                    s.close()
                    new_articles = 0
                    for entry in feed["entries"]:
                        if not self.running:
                            break
                        new_articles += self.add_entry(entry, source)
                    self.log("Done %i of %i: %s" % (i,
                        len(self.config.get_abos()), feedurl))
                    somethings += new_articles
                if callback:
                    callback(feedurl, title)
            except Exception, e:
                print e

        return somethings

    def get_quickhash(self, feedurl):
        """Fast value for comparisons without hashing"""
        h = None
        tries = 4
        while tries and h is None:
            try:
                f = open(self.cache[feedurl], "r")
                h = str(hash(f.read()))
                print h, feedurl, f.read(), h
                f.close()
            except IOError:
                tries -= 1
        return h

    def update_all(self):
        """
        Puts all feeds into the download queue to be downloaded.
        Needs some DLers in downloaders list
        """
        urls = self.config.get_abos()
        self.cache.get_all(urls, delete=True)
        s = get_session(self.db)
        for url in urls:
            if not self.running:
                break
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
        return self.download_feed(urls)

    def add_url(self, url):
        """Adds a feed url to the abos
        """
        try:
            self.config.add_abo(url)
            s = get_session(self.db)
            source = Source(url, None)
            s.add(source)
            s.commit()
            s.close()
        except Exception, e:
            print str(e)

    def remove_url(self, url):
        """Removes a feed url from the abos
        """
        self.config.del_abo(url)


@cli.daemon.DaemonizingApp
def anchorbot(app):
    bot = Anchorbot(
            not app.params.verbose,
            app.params.cache)
    atexit.register(bot.shutdown)

    if app.params.add:
        print "Adding:", app.params.add

    if app.params.daemonize:
        app.log.info("About to daemonize")
        app.daemonize()
        bot.run()
    else:
        bot.run()


anchorbot.add_param("-c", "--cache", help="only print cache", 
        default=False, action="store_true")
anchorbot.add_param("-a", "--add", help="add new urls",
        default=False, type=str)


if __name__ == "__main__":
    anchorbot.run()
