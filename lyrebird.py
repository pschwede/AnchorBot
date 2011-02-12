#!/usr/bin/env python

import feedparser, sys, os
import gtk, gtk.gdk
import webkit
import threading

HOME = os.path.realpath("./") # TODO
HTML = os.path.join(HOME, "index.html")
__appname__ = "LyreBird 0.1"
__author__ = "spazzpp2"

def log(text):
    print text

def _(text):
    return text

class lyrebird(object):
    def __init__(self):
        self.feedurls = []
        self.feeds = {}

        window = self.window = gtk.Window()
        window.set_title("Coccatoo 0.1")
        window.connect("destroy", self.quit)
        window.resize(800,600)

        vbox = self.vbox = gtk.VBox(True, 0)
        vbox.set_homogeneous(False)
        window.add(vbox)

        toolbar = gtk.Toolbar()
        new_tool = gtk.ToolButton(gtk.STOCK_ADD)
        new_tool.connect("clicked", lambda w:self.new_feed_dialog())
        toolbar.add(new_tool)

        refresh_tool = gtk.ToolButton(gtk.STOCK_REFRESH)
        refresh_tool.connect("clicked", lambda w: self.refresh())
        toolbar.add(refresh_tool)

        vbox.pack_start(toolbar, False, True)

        scroller = gtk.ScrolledWindow()
        browser = self.browser = webkit.WebView()
        scroller.add(browser)
        vbox.pack_start(scroller, expand=True, fill=True)
        
        self.refresh()
        self.window.show_all()

    def quit(self, stuff):
        gtk.main_quit()

    def refetch(self, feedurl):
        self.feeds[feedurl] = feedparser.parse(feedurl)

    def new_feed_dialog(self):
        pass

    def refresh(self):
        for url in self.feedurls:
            self.refetch(url)
        log("Writing to %s" % HTML)
        f = open(HTML, "w")
        f.write("""<head>
            <meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/></head>
            <body>""")
        for feed in self.feeds.values():
            for entry in feed['entries']:
                f.write("<h2>"+entry['title']+"</h2>")
                f.write(entry['summary_detail']['value'])
        f.write("</body>")
        f.close()
        log("Showing %s in browser" % HTML)
        self.browser.open(HTML)

    def add_url(self, url):
        self.feedurls.append(url)

    def sub_url(self, url):
        self.feedurls.remove(url)


if __name__ == "__main__":
    l = lyrebird()
    l.add_url("http://spz.kilu.de/blog/?rss=1")
    l.add_url("http://identi.ca/api/statuses/friends_timeline/spz.rss")
    gtk.main()
