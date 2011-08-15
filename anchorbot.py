#!/usr/bin/env python
# -*- encoding: utf-8 -*-

"""
This is the main file of AnchorBot, the feed reader that makes you read 
the important news first.

For further reading, see README.md
"""

import feedparser, sys, os, urllib, argparse
import gtk, gtk.gdk, gobject
import webbrowser
from tempfile import gettempdir
from traceback import print_tb
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql.expression import desc

from util import browser, analyzer, storage, _
from util.logger import Logger
from util.config import Config
from util.microblogging import Microblogger
from util.crawler import Crawler
from util.widgets import main_window
from util.datamodel import get_session, get_engine, Source, Article, Image, Keyword
from util.analyzer import Analyzer

from util.processor import Processor
from multiprocessing import Lock

from time import time

HOME = os.path.join( os.path.expanduser( "~" ),".anchorbot" )
HERE = os.path.realpath( os.path.dirname( __file__ ) )
TEMP = os.path.join( HOME, "cache/" )
HTML = os.path.join( HOME, "index.html" )
NUMT = 2
__appname__ = "AnchorBot"
__version__ = "1.0"
__author__ = "spazzpp2"

class Anchorbot( object ):
    """ The most main Class

    It holds and calls initialization of:
    * singleton instance lock
    * main window
    * configurations
    * feed downloads
    * start analysis of the downloaded feeds
    """

    def __init__( self, nogui=False, verbose=False, cache_only=False ):
        self.verbose = verbose
        self.l = l = Logger(verbose, write=os.path.join(HOME, "lyrebird.log"))

        # prepare lock, config, cache and variables
        try:
            # load config
            try:
                self.config = Config( HOME, verbose=self.verbose ) # Raises Exception if locked
            except Exception, e:
                print "It seems as if Lyrebird is already running. If not, please remove ~/.lyrebird/lock"
                raise e

            # prepare cached browser
            self.browser = browser.WebkitBrowser( HERE )
            self.browser.set_about_handler( self.__about )
            self.cache = storage.FileCacher( TEMP, 3 , False) #self.verbose) # keeps files for 3 days

            # prepare datamodel
            path = os.path.join(HOME,"database.sqlite")
            self.db = get_engine(path)

            # prepare variables and lists,...
            self.feeds = {}
            self.watched = None
            self.mblog = Microblogger()
            self.analyzer = Analyzer(key="title",eid="link")
            self.crawler = Crawler(self.cache, self.analyzer)
            self.crawler.verbose = self.verbose
            self.window = main_window( {
                    "__appname__": __appname__,
                    "__version__": __version__,
                    "__author__":  __author__,
                }, self )

            # start daemons that can download
            self.dblock = Lock()
            self.downloader = Processor(NUMT, self.download, self.update_feeds_tree)
            # in background, make daemons download feeds
            #self.downloader.run_threaded( self.update_all, self.update_feeds_tree )
        except IOError:
            sys.exit( 1 )

        # print out cache and exit
        if cache_only:
            self.__print_cache_and_exit()

    def __print_cache_and_exit( self ):
        """ well, prints cache and exits """
        self.downloader.running=False
        # print
        self.cache.pprint()
        # quit
        self.cache.quit()
        self.config.quit()
        sys.exit(0)

    def __about( self, uri ):
        """handles "about:"-url-requests."""
        if uri.startswith( "about:" ):
            print uri
            cmd = uri[6:]
            if cmd is "about":
                self.show_about()
            elif cmd.startswith( "share?" ):
                url, text = None, None
                for arg in cmd[6:].split( "&" ):
                    if arg.startswith( "url=" ):
                        url = urllib.unquote( arg[4:] )
                    if arg.startswith( "text=" ):
                        text = urllib.unquote( arg[5:] )
                if text or url:
                    self.l.log( 'Tweet %s %s' % ( text, url,  ) )
                    self.mblog.send_text( self.window, "%s %s" % ( text, url,  ) )
            elif cmd.startswith("start"):
                self.show_start()
            elif cmd.startswith("more?key="):
                s = get_session(self.db)
                arts = s.query(Article).join(Article.keywords).filter(Keyword.ID == int(cmd[9:])).order_by(Article.date).all()
                self.browser.open_articles(arts, mode=0)
                s.close()

    def update_feeds_tree( self, url, title=None ):
        """Redraws the Feed-Tree
        """
        title = title or url
        # removes old entry with url and appends a new one
        gtk.gdk.threads_enter()
        # find title or set title to url
        if url in self.window.treedic.keys():
            self.window.groups.get_model().set( self.window.treedic[url], 0, title, 1, url )
        else:
            self.window.treedic[url] = self.window.groups.get_model().append( self.window.treedic["Feeds"], [title, url] )
        self.window.groups.expand_all()
        gtk.gdk.threads_leave()
        s = get_session(self.db)
        source = s.query(Source).filter(Source.link == url).first()
        source.quickhash = self.get_hash(url)
        source.title = title
        s.commit()

    def quit( self, stuff=None ):
        """Does a save quit"""
        # stop downloading
        self.downloader.running = False
        # quit
        self.cache.quit()
        self.config.quit()
        gtk.main_quit()

    def enrich(self, entries, source):
        for entry in entries:
            url = self.crawler.get_link(entry)
            s = get_session(self.db)
            article = s.query(Article).filter(Article.link == url).first()
            s.close()
            if not article:
                tries = 10
                while tries > 0:
                    s = get_session(self.db)
                    article, keywords = self.crawler.enrich(entry, source)
                    if keywords and tries == 10:
                        article.set_keywords([s.query(Keyword).filter(Keyword.word == kw.word).first() or kw for kw in keywords])
                    if article.image:
                        if article.image in s:
                            s.expunge(article.image)
                        img = s.query(Image).filter(Image.filename == article.image.filename).first()
                        if img:
                            article.image = img
                    try:
                        s.merge(article)
                        s.commit()
                        tries = 0
                    except IntegrityError, e:
                        s.rollback()
                        tries -= 1
                        print "No success %i, %s @%s" % (tries, e, url)
                    finally:
                        s.close()

    def download( self, feedurl, callback=None):
        """Download procedure"""
        feed = self.feeds[feedurl] = feedparser.parse( self.cache[feedurl] )
        s = get_session(self.db)
        source = s.query(Source).filter(Source.link == feedurl).first()
        try:
            title = source.title = feed["feed"]["title"]
        except KeyError:
            title = source.title = u""
        s.close()
        
        # make DLer start some processes to enrich entries
        self.downloader.map(self.enrich, feed["entries"], source)

        self.l.log("Done %i of %i" % (self.feeds.keys().index(feedurl)+1, len( self.feeds ),))
        if callback:
            callback(feedurl, title)

    def get_hash(self, feedurl):
        """Fast value for comparisons without hashing"""
        del self.cache[feedurl]
        f = open(self.cache[feedurl])
        h = hash(f.read())
        f.close()
        return h

    def update_all(self, callback=None):
        """Puts all feeds into the download queue to be downloaded.
        Needs some DLers in downloaders list
        """
        for url in self.config.get_abos():
            s = get_session(self.db)
            source = s.query(Source).filter(Source.link == url).first()
            if not source:
                self.l.log( "New source: %s" % url)
                source = Source(url)
                s.add(source)
                try:
                    s.commit()
                except IntegrityError:
                    s.rollback()
                    self.l.log("Couldn't store source %s" % source)
             
            h = self.get_hash(url)
            if not source.quickhash or h != source.quickhash:
                self.l.log( "Something new: %s" % url)
                # throw url before the daemons
                self.downloader.run_one(url)
            else:
                if callback:
                    callback(source.link, source.title)
                self.l.log("Nothing new: %s" % url)
                s.close()

    def show_start(self, dtime=24*3600):
        s = get_session(self.db)
        for art in s.query(Article).filter(Article.date > time() - dtime).all():
            self.analyzer.add({"title":art.title, "link":art.link})
        self.analyzer.get_keywords_of_articles()
        print self.analyzer.keywords
        arts = []
        for score, url in sorted(self.analyzer.popularity.items(), reverse=True):
            arts.append(s.query(Article).filter(Article.link == url).first())
        self.browser.open_articles(arts)
        s.close()

    def show( self, url=None ):
        """Shows url in browser. If url is already shown in browser,
        the feed will be downloaded again.
        """
        if not url and self.watched:
            url = self.watched
        if url:
            if url.startswith("about:"):
                self.__about(url)
                return
            s = get_session(self.db)
            if url == self.watched:
                source = s.query(Source).filter(Source.link == url).first()
                self.downloader.run_one(url, self.update_feeds_tree)
            # but also reload the view
            articles = s.query(Article).join(Article.source).filter(Source.link == url).order_by(desc(Article.date)).all()
            self.browser.open_articles( articles )
            s.close()
        else:
            self.downloader.run_threaded( self.update_all, self.update_feeds_tree )
        self.watched = url

    def add_url( self, url ):
        """Adds a feed url to the abos
        """
        self.config.add_abo( url )
        self.downloader.map( self.download, [url], self.update_feeds_tree )
        s = get_session(self.db)
        source = Source(url, None)
        s.add(source)
        s.commit()

    def remove_url( self, url ):
        """Removes a feed url from the abos
        """
        self.config.del_abo( url )
        self.update_feeds_tree( url )

def main( urls=[], nogui=False, cache_only=False, verbose=False ):
    """The main func which creates Lyrebird
    """
    gobject.threads_init()
    l = Anchorbot(nogui, cache_only, verbose)
    gobject.idle_add( l.show )
    for url in urls:
        gobject.idle_add( l.add_url, ( url, ) )
    gtk.main()

def get_cmd_options():
    usage = "lyrebird.py"

if __name__ == "__main__":
    if len( sys.argv ) > 1:
        if len(sys.argv) > 1:
            main(   sys.argv[1:] if "-a" in sys.argv else [],
                    "-n" in sys.argv, # no-gui option
                    "-v" in sys.argv, # verbose option
                    "-c" in sys.argv )# print cache only
    else:
        main()
