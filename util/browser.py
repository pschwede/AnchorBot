import gtk, gobject, os, urllib, webbrowser
import widgets
from logger import log

try:
    import webkit
    WEBKIT = True
except:
    WEBKIT = False

class TextBrowser(gtk.TextView):
    def __init__(self):
        super(TextBrowser, self).__init__()
        self.set_editable(False)
        self.set_cursor_visible(False)
        self.set_justification(gtk.JUSTIFY_FILL)
        self.set_left_margin(10)
        self.set_right_margin(10)
        self.news = gtk.VBox()
        scroller = gtk.ScrolledWindow()
        scroller.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scroller.add_with_viewport(self.news)

    def open(self, url):
        f = urllib.urlopen(url)
        self.get_buffer().set_text(u"".join(f.readlines()))
        f.close()

    def openfeed(self, feed):
        for entry in feed['entries']:
            entry["image"] = None
            gtk.gdk.threads_enter()
            # TODO News widget
            # Big and smaller ones.. think about it for a while..
            w = gtkSmallWidget(entry)
            w.show()
            self.news.add(w)
            gtk.gdk.threads_leave()
            
class WebkitBrowser(gtk.ScrolledWindow):
    def __init__(self, absolute="", style="default.css"):
        super(WebkitBrowser, self).__init__()
        self.absolute = absolute
        self.set_shadow_type(gtk.SHADOW_IN)
        self.browser = webkit.WebView()
        self.browser.connect("navigation-policy-decision-requested", 
                self._navigation_requested)
        self.add(self.browser)
        self.browser.show()
        self.html = ""
        self.about_handler = None
        self._style = os.path.join(self.absolute, "style/%s" % style)

    def _navigation_requested(self, view, frame, req, act, pol):
        url = req.get_uri()
        if url.startswith("about:"):
            if self.about_handler:
                self.about_handler(url)
        elif url.startswith("file:") or url.startswith("embed"):
            pol.use()
        else:
            print "Opening %s in standard browser." % url
            webbrowser.open(url)
            pol.ignore()
        return True

    def set_about_handler(self, handlefunc):
        self.about_handler = handlefunc

    def open(self, uri):
        self.browser.open(uri)

    def open_article(self, article):
        self.html = """<!doctype html><html lang="en de"><head>
        <link rel="stylesheet" type="text/css" href="%s"/>
        <script type="text/javascript" src="file://%s/third-party/%s"></script>
        </head>
        <body>""" % (
                self._style,
                self.absolute, 'jquery-1.5.min.js',
                )
        self.html += str(widgets.htmlArticleWidget(article, dominance=0))
        self.html += "</body></html>"
        f = open("/tmp/browser.html", 'w')
        f.write(self.html)
        f.close()
        self.browser.load_string(self.html, "text/html", "utf-8", "file:///")

    def open_articles(self, list_of_articles, write="/tmp/browser.html"):
        loa = list_of_articles
        self.html = """<!doctype html><html lang="en de"><head>
        <link rel="stylesheet" type="text/css" href="%s"/>
        <script type="text/javascript" src="file://%s/third-party/%s"></script>
        </head>
        <body>""" % (
                self._style,
                self.absolute, 'jquery-1.5.min.js',
                )
        for article in loa:
            self.html += str(widgets.htmlArticleWidget(article))
        self.html += "</body></html>"
        self.browser.load_string(self.html, "text/html", "utf-8", "file:///")
        if write:
            f = open(write, 'w')
            f.write(self.html)
            f.close()
