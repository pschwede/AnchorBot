import gtk, os, webbrowser
from templates import article as temp_art

try:
    import webkit
    WEBKIT = True
except:
    WEBKIT = False

class WebkitBrowser( gtk.ScrolledWindow ):
    html_template = """<!doctype html>
        <html lang="en de">
            <head>
                <meta http-equiv="content-type" content="text/html; charset=UTF-8">
                <link rel="stylesheet" type="text/css" href="%s"/>
                <script type="text/javascript" src="file://%s/third-party/%s"></script>
            </head>
            <body>
                %s
            </body>
        </html>"""
    def __init__( self, absolute="", style="default.css" ):
        super( WebkitBrowser, self ).__init__()
        self.absolute = absolute
        self.set_shadow_type( gtk.SHADOW_IN )
        self.browser = webkit.WebView()
        self.browser.connect( "navigation-policy-decision-requested",
                self._navigation_requested )
        self.add( self.browser )
        self.browser.show()
        self.html = ""
        self.about_handler = None
        self._style = os.path.join( self.absolute, "style/%s" % style )
        print self._style

    def _navigation_requested( self, view, frame, req, act, pol ):
        url = req.get_uri()
        if url.startswith( "about:" ):
            if self.about_handler:
                self.about_handler( url )
        elif url.startswith( "file:" ) or url.startswith( "embed" ):
            pol.use()
        else:
            print "Opening %s in standard browser." % url
            webbrowser.open( url )
            pol.ignore()
        return True

    def set_about_handler( self, handlefunc ):
        self.about_handler = handlefunc

    def open( self, uri ):
        self.browser.open( uri )

    def open_articles( self, list_of_articles, write="/tmp/browser.html", mode=1 ):
        loa = list_of_articles
        content = u""
        for article in loa:
            content += temp_art( article, mode )
        self.html = self.html_template % ( 
                self._style,
                self.absolute, 'jquery-1.5.min.js',
                content,
                )
        self.browser.load_string( self.html, "text/html", "utf-8", "file:///" )
        if write:
            f = open( write, 'w' )
            f.write( self.html )
            f.close()
