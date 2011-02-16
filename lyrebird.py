#!/usr/bin/env python

import feedparser, sys, os
import gtk, gtk.gdk, gobject
from util import browser, analyzer, storage, _
from util.logger import log
from util.config import Config
import threading
import webbrowser

HOME = os.path.join(os.path.expanduser("~"),".lyrebird")
HERE = os.path.realpath(os.path.dirname(__file__))
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
        self.cache = storage.PersistentCacher()
        self.feeds = {}
        self.watched = None

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
        self.feeds_iter = groups_model.append(None, [_("Feeds"), None])
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

    def update_feeds_tree(self, url):
        gtk.gdk.threads_enter()
        try:
            feed = self.feeds[url]
            self.groups.get_model().append(self.feeds_iter, [feed["feed"]["title"], url])
        except KeyError:
            self.groups.get_model().remove(self.feeds_iter)
            self.feeds_iter = self.groups.get_model().append(None, [_("Feeds"), None])
            for url,feed in self.feeds.items(): #TODO find a better way
                self.groups.get_model().append(self.feeds_iter, [feed["feed"]["title"], url])
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

    def quit(self, stuff):
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
        if callback:
            callback(feedurl)

    def download_all(self, callback=None):
        if callback:
            for url in self.config.get_abos():
                threading.Thread(target=self.download, args=(url,False,lambda x: callback(x))).start()
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
            #self.browser.openfeed(self.feeds.values()[-1])
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

def main():
    gobject.threads_init()
    l = lyrebird()
    gobject.idle_add(l.show)
    #gobject.idle_add(l.update_feeds_tree)
    gtk.main()

def get_cmd_options():
    usage = "lyrebird.py"

if __name__ == "__main__":
    main()
