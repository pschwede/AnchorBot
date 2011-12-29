#!/usr/bin/env python
# -*- encoding: utf-8 -*-

"""
This is the main file of AnchorBot, the feed reader that makes you read
the important news first.

For further reading, see README.md
"""

import feedparser
import sys
import os
import urllib
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql.expression import desc

from util import browser, storage
from util.logger import Logger
from util.config import Config
from util.microblogging import Microblogger
from util.crawler import Crawler
from util.widgets import main_window
from util.datamodel import (get_session,
                                get_engine, Source, Article, Image, Keyword)
from util.analyzer import Analyzer

from util.processor import Processor
from multiprocessing import Lock
import gobject
import gtk
import gtk.gdk

from time import time, sleep

HOME = os.path.join(os.path.expanduser("~"), ".anchorbot")
HERE = os.path.realpath(os.path.dirname(__file__))
TEMP = os.path.join(HOME, "cache/")
HTML = os.path.join(HOME, "index.html")
NUMT = 2
__appname__ = "AnchorBot"
__version__ = "1.1"
__author__ = "spazzpp2"


class Anchorbot(object):
    """ The most main Class

    It holds and calls initialization of:
    * singleton instance lock
    * main window
    * configurations
    * feed downloads
    * start analysis of the downloaded feeds
    """

    def __init__(self, nogui=False, verbose=False, cache_only=False, update_call=lambda x:x):
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
            self.mblog = Microblogger()
            self.analyzer = Analyzer(key="title", eid="link")
            self.crawler = Crawler(self.cache, self.analyzer)
            self.crawler.verbose = self.verbose
            self.dblock = Lock()
            if not nogui:
                # prepare cached browser
                self.browser = browser.WebkitBrowser(HERE)
                self.browser.set_about_handler(self.__about)
                self.window = main_window({
                        "__appname__": __appname__,
                        "__version__": __version__,
                        "__author__":  __author__,
                }, self)

                # start daemons that can download
                self.downloader = Processor(NUMT, self.download, self.update_feeds_tree)
                # in background, make daemons download feeds
                self.running, self.timeout = True, 3000 #TODO load from config
                self.downloader.run_threaded(self.update_all, self.update_feeds_tree)
            else:
                # start daemons that can download
                self.downloader = Processor(NUMT, self.download, update_call)
                # in background, make daemons download feeds
                self.running, self.timeout = True, 3000 #TODO load from config
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

    def __about(self, uri):
        """handles "about:"-url-requests."""
        if uri.startswith("about:"):
            cmd = uri[6:]
            if cmd is "about":
                self.show_about()
            elif cmd.startswith("share?"):
                url, text = None, None
                for arg in cmd[6:].split("&"):
                    if arg.startswith("url="):
                        url = urllib.unquote(arg[4:])
                    if arg.startswith("text="):
                        text = urllib.unquote(arg[5:])
                if text or url:
                    self.log('Tweet %s %s' % (text, url,))
                    self.mblog.send_text(self.window, "%s %s" % (text, url,))
            elif cmd.startswith("start"):
                self.show_start()
            elif cmd.startswith("more?key="):
                ID = int(cmd[9:])
                s = get_session(self.db)
                kw = s.query(Keyword).filter(Keyword.ID == ID).first()
                kw.clickcount += 1
                s.merge(kw)
                s.commit()
                arts = s.query(Article).join(Article.keywords).filter(Keyword.ID == ID).order_by(Article.date).all()
                self.browser.open_articles(arts, mode=0)
                s.close()

    def update_feeds_tree(self, url, title=None):
        """Redraws the Feed-Tree
        """
        title = title or url
        # removes old entry with url and appends a new one
        gtk.gdk.threads_enter() #@UndefinedVariable
        # find title or set title to url
        if url in self.window.treedic.keys():
            self.window.groups.get_model().set(self.window.treedic[url], 0, title, 1, url)
        else:
            self.window.treedic[url] = self.window.groups.get_model().append(self.window.treedic["Feeds"], [title, url])
        self.window.groups.expand_all()
        gtk.gdk.threads_leave() #@UndefinedVariable
        s = get_session(self.db)
        source = s.query(Source).filter(Source.link == url).first()
        source.quickhash = self.get_hash(url)
        source.title = title
        s.commit()

    def shutdown(self, stuff=None):
        """Does a save shutdown"""
        # stop downloading
        self.running = False
        self.downloader.running = False
        # shutdown
        self.cache.shutdown()
        self.config.shutdown()
        try:
            gtk.main_quit()
        except:
            pass

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

    def show_start(self, dtime=24 * 3600):
        # add articles of most clicked keywords
        s = get_session(self.db)
        keywords = s.query(Keyword).order_by(desc(Keyword.clickcount)).limit(10)
        for kw in set(keywords):
            clickedarts = s.query(Article).filter(Article.keywords.contains(kw)).filter(Article.date > time() - 24 * 3600).all() #TODO last-visited @UndefinedVariable
            newarts = s.query(Article).filter(Article.date > time() - 24 * 3600).all() #TODO last-visited @UndefinedVariable
        self.browser.open_articles(sorted(list(set(clickedarts) | set(newarts)), key=lambda x: x.date))
        s.close()

    def show(self, url=None):
        """Shows url in browser. If url is already shown in browser,
        the feed will be downloaded again.
        """
        if not url and self.watched:
            url = self.watched
        if url:
            if url.startswith("about:"):
                self.__about(url)
                return
            if url == self.watched:
                self.downloader.run_one(url, self.update_feeds_tree)
            else:
                s = get_session(self.db)
                articles = s.query(Article).join(Article.source).filter(Source.link == url).order_by(desc(Article.date)).all()
                self.browser.open_articles(articles)
                s.close()
        else:
            pass #self.downloader.run_threaded(self.update_all, self.update_feeds_tree)
        self.watched = url

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

def main(urls=[], nogui=False, cache_only=False, verbose=False):
    """The main func which creates Lyrebird
    """
    gobject.threads_init() #@UndefinedVariable
    l = Anchorbot(nogui, cache_only, verbose)
    gobject.idle_add(l.show)
    for url in urls:
        gobject.idle_add(l.add_url, (url,))
    gtk.main()


def get_cmd_options():
    usage = "anchorbot.py"
    return usage

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if len(sys.argv) > 1:
            main(sys.argv[1:] if "-a" in sys.argv else [],
                    "-n" in sys.argv, # no-gui option
                    "-v" in sys.argv, # verbose option
                    "-c" in sys.argv)# print cache only
    else:
        main()
