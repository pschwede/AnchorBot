#!/usr/bin/env python

import feedparser, sys, os
import gtk, gtk.gdk, gobject
from util import browser, analyzer, storage, _
from util.logger import log
import threading
import webbrowser
import pango

HOME = os.path.realpath("./") # TODO
HTML = os.path.join(HOME, "index.html")
__appname__ = "Lyrebird"
__version__ = "0.1 Coccadoo"
__author__ = "spazzpp2"

class lyrebird(object):
    def __init__(self, nogui=False):
        self.feedurls = []
        self.feeds = {}
        self.browser = browser.WebkitBrowser()
        self.browser.set_about_handler(self.__about)
        self.cache = storage.PersistentCacher()

        window = self.window = gtk.Window()
        window.set_title(__appname__+" "+__version__)
        window.connect("destroy", self.quit)

        hbox = self.hbox = gtk.HBox(False, 0)

        # BEGIN toolbar

        toolbar = gtk.Toolbar()
        toolbar.set_orientation(gtk.ORIENTATION_VERTICAL)
        hbox.pack_start(toolbar, False, True)

        new_tool = gtk.ToolButton(gtk.STOCK_ADD)
        new_tool.connect("clicked", lambda w:self.new_feed_dialog())
        toolbar.add(new_tool)

        refresh_tool = gtk.ToolButton(gtk.STOCK_REFRESH)
        refresh_tool.connect("clicked", lambda w: self.refresh())
        toolbar.add(refresh_tool)

        quit_tool = gtk.ToolButton(gtk.STOCK_QUIT)
        quit_tool.connect("clicked", self.quit)
        toolbar.add(quit_tool)

        about_tool = gtk.ToolButton(gtk.STOCK_ABOUT)
        about_tool.connect("clicked", self.show_about)
        toolbar.add(about_tool)

        # END toolbar

        hpaned = gtk.HPaned()
        hbox.pack_start(hpaned, True, True)

        # BEGIN groups

        groups = gtk.TreeView()

        self.groups = gtk.TreeStore(str,str)
        groups.set_model(self.groups)

        cat_cell = gtk.CellRendererText()
        cat_column = gtk.TreeViewColumn(_('Category'))
        cat_column.pack_start(cat_cell, True)
        cat_column.add_attribute(cat_cell, 'text', 0)
        groups.append_column(cat_column)

        itm_cell = gtk.CellRendererText()
        itm_column = gtk.TreeViewColumn(_('Item'))
        itm_column.pack_start(itm_cell, True)
        itm_column.add_attribute(itm_cell, 'text', 1)
        groups.append_column(itm_column)

        scroller = gtk.ScrolledWindow()
        scroller.add_with_viewport(groups)
        hpaned.pack1(scroller)

        # END groups

        vbox = gtk.VBox()
        vbox.pack_start(hbox, True, True)
        
        hpaned.pack2(self.browser) # browser defined above
        hpaned.set_position(0)
        
        self.status = gtk.Statusbar()
        vbox.pack_start(self.status, False, True)

        self.window.add(vbox)
        self.window.set_size_request(640, 480)
        self.window.show_all()

    def __about(self, uri):
        if not uri.startswith("about:"):
            return
        else:
            cmd = uri[6:]
            if cmd == "about":
                self.show_about()
            elif cmd.startswith("thumbs_up"):
                pass #TODO retweet and stuff

    def show_group(self, url):
        self.browser.openfeed(url)

    def update_groups(self):
        gtk.gdk.threads_enter()
        self.groups.clear() # TODO find a better way
        self.groups.append(None, ["Feeds", None])
        piter = self.groups.get_iter((0, ))
        for url,fdic in self.feeds.items():
            self.groups.append(piter, [fdic["feed"]["title"], url])
        gtk.gdk.threads_leave()

    def show_about(self, stuff=None):
        ad = gtk.AboutDialog()
        ad.set_program_name(__appname__)
        ad.set_version(__version__)
        ad.set_authors([__author__])
        ad.set_copyright(__author__)
        ad.run()
        ad.destroy()

    def quit(self, stuff):
        gtk.main_quit()

    def refetch(self, feedurl, cached=True):
        if cached:
            self.feeds[feedurl] = feedparser.parse(self.cache[feedurl])
        else:
            self.feeds[feedurl] = feedparser.parse(feedurl)

    def new_feed_dialog(self):
        pass

    def refresh(self):
        for url in self.feedurls:
            self.refetch(url)
        log("Writing to %s" % HTML)
        #TODO analyze first
        self.browser.openfeed(self.feeds.values()[0])

    def add_url(self, url):
        self.feedurls.append(url)
        self.update_groups()

    def sub_url(self, url):
        self.feedurls.remove(url)
        self.update_groups()

def main():
    gobject.threads_init()
    l = lyrebird()
    l.add_url("http://www.dnn-online.de/rss/dresden-rss.xml")
    l.add_url("http://www.heise.de/newsticker/heise-atom.xml")
    gobject.idle_add(l.refresh)
    gtk.main()

def get_cmd_options():
    usage = "lyrebird.py"

if __name__ == "__main__":
    main()
