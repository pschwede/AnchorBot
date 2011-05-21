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
    def __init__(self, absolute=""):
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

    def _navigation_requested(self, view, frame, req, act, pol):
        url = req.get_uri()
        if url.startswith("about:"):
            if self.about_handler:
                self.about_handler(url)
        elif url.startswith("file:") or ".swf" in url:
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

    def _style(self):
        return "" #TODO load from file

    def openfeed(self, feed):
        self.html = "<html><head>"
        self.html += "</head><style>"+self._style()+"</style>" 
        self.html += '<script type="text/javascript" src="file://'+self.absolute+'/third-party/jquery-1.5.min.js"></script>'
        self.html += '<body>'
        #TODO import style themes and support templates (django api?)
        for entry in feed["entries"]:
            self.html += str(widgets.htmlSmallWidget(entry))
        self.html += "</body></html>"
        f = open("/tmp/browser.html", 'w')
        f.write(self.html)
        f.close()
        self.browser.load_string(self.html, "text/html", "utf-8", "file:///")
        # TODO load stuff with js
