#!/usr/bin/env python

import feedparser, sys, os, urllib
import gtk, gtk.gdk, gobject
import threading, webbrowser
from tempfile import gettempdir

from util import browser, analyzer, storage, _
from util.logger import log
from util.config import Config
from util.microblogging import Microblogger
from util.crawler import Crawler

HOME = os.path.join(os.path.expanduser("~"),".lyrebird")
HERE = os.path.realpath(os.path.dirname(__file__))
#TEMP = os.path.join(os.path.realpath(gettempdir()), "lyrebird/")
TEMP = os.path.join(HOME, "cache/")
HTML = os.path.join(HOME, "index.html")
__appname__ = "Lyrebird"
__version__ = "0.1 Coccatoo"
__author__ = "spazzpp2"

class lyrebird(object):
    def __init__(self, nogui=False):
        try:
            self.config = Config(HOME) # Raises Exception if locked
        except:
            print _("It seams as if Lyrebird is already running. If not, please remove ~/.lyrebird/lock")
            sys.exit(1)

        self.browser = browser.WebkitBrowser(HERE)
        self.browser.set_about_handler(self.__about)
        self.cache = storage.PersistentCacher(TEMP)
        self.feeds = {}
        self.watched = None
        self.mblog = Microblogger()
        self.crawler = Crawler(self.cache)

        window = self.window = gtk.Window()
        window.set_title(__appname__+" "+__version__)
        window.connect("destroy", self.quit)

        hbox = self.hbox = gtk.HBox(False, 0)

        # BEGIN toolbar

        toolbar = gtk.Toolbar()
        toolbar.set_border_width(0)
        toolbar.set_orientation(gtk.ORIENTATION_VERTICAL)
        hbox.pack_start(toolbar, False, True)

        new_tool = gtk.ToolButton(gtk.STOCK_ADD)
        new_tool.connect("clicked", lambda w:self.new_feed_dialog())
        toolbar.add(new_tool)

        show_tool = gtk.ToolButton(gtk.STOCK_REFRESH)
        show_tool.connect("clicked", lambda w: self.download_all())
        toolbar.add(show_tool)

        conf_tool = gtk.ToolButton(gtk.STOCK_PREFERENCES)
        # connect conf_tool
        toolbar.add(conf_tool)

        about_tool = gtk.ToolButton(gtk.STOCK_ABOUT)
        about_tool.connect("clicked", self.show_about)
        toolbar.add(about_tool)

        sep_tool = gtk.SeparatorToolItem()
        sep_tool.set_expand(True)
        toolbar.add(sep_tool)

        quit_tool = gtk.ToolButton(gtk.STOCK_QUIT)
        quit_tool.connect("clicked", self.quit)
        toolbar.add(quit_tool)

        # END toolbar

        hpaned = gtk.HPaned()
        hbox.pack_start(hpaned, True, True)

        # BEGIN self.groups

        self.groups = gtk.TreeView()
        self.groups.connect("cursor_changed", self._cell_clicked)

        groups_model = gtk.TreeStore(str,str)
        self.treedic = {}
        self.treedic["Feeds"] = groups_model.append(None, [_("Feeds"), None])
        self.groups.set_model(groups_model)

        cat_cell = gtk.CellRendererText()
        cat_column = gtk.TreeViewColumn(_('Category'))
        cat_column.pack_start(cat_cell, True)
        cat_column.add_attribute(cat_cell, 'text', 0)
        self.groups.append_column(cat_column)

        itm_cell = gtk.CellRendererText()
        itm_column = gtk.TreeViewColumn(_('Item'))
        itm_column.pack_start(itm_cell, True)
        itm_column.add_attribute(itm_cell, 'text', 1)
        self.groups.append_column(itm_column)

        scroller = gtk.ScrolledWindow()
        scroller.add_with_viewport(self.groups)
        hpaned.pack1(scroller)

        # END self.groups

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
                    log('Tweet %s %s' % (text, url, ))
                    self.mblog.send_text("%s %s" % (text, url, ))

    def show_group(self, url):
        self.browser.openfeed(url)

    def update_feeds_tree(self, url):
        gtk.gdk.threads_enter()
        feed = self.feeds[url]
        if url in self.treedic.keys():
            self.groups.get_model().remove(self.treedic[url])
        title = url
        try:
            title = feed["feed"]["title"]
        except KeyError:
            log("Couldn't find [feed][title] in "+url)
        self.treedic[url] = self.groups.get_model().append(self.treedic["Feeds"], [title, url])
        self.groups.expand_all()
        gtk.gdk.threads_leave()

    def show_about(self, stuff=None):
        ad = gtk.AboutDialog()
        ad.set_program_name(__appname__)
        ad.set_version(__version__)
        ad.set_authors([__author__])
        ad.set_copyright(__author__)
        ad.run()
        ad.destroy()

    def quit(self, stuff=None):
        self.config.quit()
        gtk.main_quit()

    def new_feed_dialog(self):
        w = gtk.Window() #gtk.WINDOW_POPUP)

        table = gtk.Table(2,2)
        table.set_row_spacings(3)
        table.set_col_spacings(3)
        table.set_border_width(3)
        w.add(table)
        
        url_label = gtk.Label(_("URL:"))
        table.attach(url_label, 0, 1, 0, 1)

        url_entry = gtk.Entry()
        table.attach(url_entry, 1, 2, 0, 1)

        hbox = gtk.HBox(True)
        table.attach(hbox, 0, 2, 1, 2)

        ok = gtk.Button(stock=gtk.STOCK_OK)
        ok.connect("clicked", lambda x: (self.add_url(url_entry.get_text()), w.destroy()))
        hbox.pack_end(ok, False, False)

        cancel = gtk.Button(stock=gtk.STOCK_CANCEL)
        cancel.connect("clicked", lambda x: w.destroy())
        hbox.pack_end(cancel, False, False)

        w.show_all()

    def download(self, feedurl, cached=True, callback=None):
        if not cached:
            del self.cache[feedurl]
        self.feeds[feedurl] = feedparser.parse(self.cache[feedurl])
        for entry in self.feeds[feedurl]["entries"]:
            entry = self.crawler.enrich(entry)
        log("*** " + str(self.feeds.keys().index(feedurl)) + " of " + str(len(self.feeds)))
        if callback:
            callback(feedurl)

    def download_all(self, callback=None):
        if callback:
            for url in self.config.get_abos():
                threading.Thread(target=self.download, args=(url,False,callback)).start()
        else:
            for url in self.config.get_abos():
                threading.Thread(target=self.download, args=(url,False,None)).start()

    def show(self, url=None):
        if not url and self.watched:
            url = self.watched
        if url:
            if url == self.watched:
                self.download(url, False)
            self.browser.openfeed(self.feeds[url])
        else:
            #TODO analyze first
            self.download_all(self.update_feeds_tree)
        self.watched = url

    def _cell_clicked(self, view):
        sel = view.get_selection()
        model, piter = sel.get_selected()
        if piter:
            url = model.get_value(piter, 1)
            if url:
                self.show(url)

    def add_url(self, url):
        self.config.add_abo(url)
        self.download(url)
        self.show(url)
        self.update_feeds_tree(url)

    def remove_url(self, url):
        self.config.del_abo(url)
        self.update_feeds_tree(url)

def main(urls=[]):
    gobject.threads_init()
    l = lyrebird()
    gobject.idle_add(l.show)
    for url in urls:
        gobject.idle_add(l.add_url, (url,))
    gtk.main()

def get_cmd_options():
    usage = "lyrebird.py"

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1:])
    else:
        main()
