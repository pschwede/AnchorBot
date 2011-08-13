#!/usr/bin/env python
# -*- encoding: utf-8 -*-

"""
This is the main file of AnchorBot, the feed reader that makes you read 
the important news first.

For further reading, see README.md
"""

import feedparser, sys, os, urllib, argparse
import gtk, gtk.gdk, gobject
import threading, webbrowser, Queue
from tempfile import gettempdir
from traceback import print_tb
from sqlalchemy.exc import IntegrityError

from util import browser, analyzer, storage, _
from util.logger import Logger
from util.config import Config
from util.microblogging import Microblogger
from util.crawler import Crawler
from util.widgets import main_window
from util.datamodel import get_session, get_engine, Source, Article, Image, Keyword
from util.analyzer import Analyzer

HOME = os.path.join( os.path.expanduser( "~" ),".anchorbot" )
HERE = os.path.realpath( os.path.dirname( __file__ ) )
TEMP = os.path.join( HOME, "cache/" )
HTML = os.path.join( HOME, "index.html" )
NUMT = 6
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
            self.__prepare()
        except IOError:
            sys.exit( 1 )
        self.__setup_dl_pipes( NUMT )

        # print out cache and exit
        if cache_only:
            self.__print_cache_and_exit()

    def __prepare( self ):
        """ Checks lock, reads config, initializes cache, etc.
        
        Raises IOError-exception if Lyrebird is already running.
        """

        # load config
        try:
            self.config = Config( HOME, verbose=self.verbose ) # Raises Exception if locked
        except Exception, e:
            print "It seems as if Lyrebird is already running. If not, please remove ~/.lyrebird/lock"
            raise e

        # prepare cached browser
        self.browser = browser.WebkitBrowser( HERE )
        self.browser.set_about_handler( self.__about )
        self.cache = storage.FileCacher( TEMP, -1 , self.verbose) # keeps files for 3 days

        # prepare datamodel
        path = os.path.join(HOME,"database.sqlite")
        self.db = get_engine(path)

        # prepare variables and lists,...
        self.feeds = {}
        self.downloaders = []
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

    def __run_downloader(self):
        """run a downloader *without* caching"""
        t = threading.Thread( target=self.__dl_worker, args=( self.update_feeds_tree,  ) )
        t.daemon = True
        t.start()
        self.downloaders.append(t)

    def __setup_dl_pipes( self, number_of_pipes ):
        """ initializes a list of Download Threads and a Queue.Queue """
        # setup download pipes
        self.dl_queue = Queue.Queue()
        self.dl_running = True
        for i in range( number_of_pipes ):
            self.__run_downloader()

    def __print_cache_and_exit( self ):
        """ well, prints cache and exits """
        # kill all threads
        self.dl_running = False
        # print
        self.cache.pprint()
        # quit
        self.cache.quit()
        self.config.quit()
        sys.exit(0)

    def __about( self, uri ):
        """handles "about:"-url-requests.
        """
        if uri.startswith( "about:" ):
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

    def update_feeds_tree( self, title, url=None ):
        """Redraws the Feed-Tree
        """
        url = url or title
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
        s.commit()

    def quit( self, stuff=None ):
        """Does a save Quit
        """
        # stop downloading
        self.dl_running = False
        # quit
        self.cache.quit()
        self.config.quit()
        gtk.main_quit()

    def __dl_worker( self, callback=None ):
        """Method for download threads
        Setting self.dl_running to False would stop them all.
        """
        while self.dl_running:
            url = self.dl_queue.get()
            self.download( url, callback )
            self.dl_queue.task_done()

    def download( self, feedurl, callback=None):
        """Download procedure"""
        feed = self.feeds[feedurl] = feedparser.parse( self.cache[feedurl] )
        s = get_session(self.db)
        source = s.query(Source).filter(Source.link == feedurl).first()
        title = source.title = feed["feed"]["title"]
        s.close()
        for entry in feed["entries"]:
            url = self.crawler.get_link(entry)
            s = get_session(self.db)
            article = s.query(Article).filter(Article.link == url).first()
            if not article:
                article = self.crawler.enrich(entry, source)
                s.add(article)
                try:
                    s.commit()
                except IntegrityError, e:
                    s.rollback()
                    self.l.log("IntegrityError: %s" % e)
                print s.query(Article).filter(Article.link == url).first()
            s.close()
        self.l.log("Done %i of %i" % (self.feeds.keys().index(feedurl)+1, len( self.feeds ),))
        if callback:
            callback(title, feedurl)

    def get_hash(self, feedurl):
        del self.cache[feedurl]
        f = open(self.cache[feedurl])
        h = hash(f.read())
        f.close()
        return h

    def __download_all(self, callback=None):
        """Puts all feeds into the download queue to be downloaded.
        Needs some DLers in downloaders list
        """
        for url in self.config.get_abos():
            s = get_session(self.db)
            source = s.query(Source).filter(Source.link == url).first()
            if not source:
                print "New source: %s" % url
                source = Source(url)
                s.add(source)
                try:
                    s.commit()
                except IntegrityError:
                    s.rollback()
             
            h = self.get_hash(url)
            if not source.quickhash or h != source.quickhash:
                print "Something new: %s" % url, h, source.quickhash
                if len(self.downloaders) >= NUMT:
                    self.dl_queue.put_nowait(url)
                else:
                    self.download_one(url, callback)
            else:
                print "Nothing new: %s" % url, h
                if callback:
                    callback(source.title, source.link)
                self.l.log("Nothing new: %s" % url)
                s.close()

    def download_all( self, callback=None ):
        """Threaded wrapper around __download_all"""
        t = threading.Thread( target=self.__download_all, args=( self.update_feeds_tree,  ) )
        t.daemon = True
        t.start()

    def download_one( self, url, callback=None ):
        self.dl_queue.put_nowait( url )
        self.__run_downloader() # Careful with this, since they could get more and more here

    def show( self, url=None ):
        """Shows url in browser. If url is already shown in browser,
        the feed will be downloaded again.
        """
        if not url and self.watched:
            url = self.watched
        if url:
            s = get_session(self.db)
            if url == self.watched:
                source = s.query(Source).filter(Source.link == url).first()
                self.download_one(url, self.update_feeds_tree)
            # but also reload the view
            articles = s.query(Article).join(Article.source).filter(Source.link == url).all()
            self.browser.open_articles( articles )
            s.close()
        else:
            self.download_all( self.update_feeds_tree )
        self.watched = url

    def add_url( self, url ):
        """Adds a feed url to the abos
        """
        self.config.add_abo( url )
        self.download_one( url, self.update_feeds_tree )
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