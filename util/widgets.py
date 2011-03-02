import gtk, pango
from logger import log
#TODO import _

class tweet_window(gtk.Dialog):
    def __init__(self, service=None, user=None, password=None, text=None):
        super(tweet_window, self).__init__()
        self.user, self.__password = user, password
        self.service = service

        table = gtk.Table()
        self.vbox.pack_start(table)

        self.serv_label = gtk.Label(service)
        table.attach(self.serv_label, 0,2,0,1)

        self.user_label = gtk.Label("Name:")
        table.attach(self.user_label, 0,1,1,2)
        self.user_entry = gtk.Entry()
        table.attach(self.user_entry, 1,2,1,2)

        self.user_label = gtk.Label("Password:")
        table.attach(self.user_label, 0,1,2,3)
        self.user_password = gtk.Entry()
        self.user_password.set_visibility(False)
        table.attach(self.user_password, 1,2,2,3)

        scrolled = gtk.ScrolledWindow()
        self.text_buf = gtk.TextBuffer()
        self.text_buf.set_text(text)
        textv = gtk.TextView(self.text_buf)
        textv.set_wrap_mode(gtk.WRAP_WORD_CHAR)
        scrolled.add(textv)
        table.attach(scrolled, 0,2,3,4)

        table.show_all()
        self.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        self.add_button(gtk.STOCK_YES, gtk.RESPONSE_OK)

    def run(self):
        resp = super(tweet_window, self).run()
        if resp == gtk.RESPONSE_OK:
            self.hide()
            return (self.user_entry.get_text(), self.user_password.get_text(), self.text_buf.get_text())
        else:
            self.hide()
            return None

class htmlSmallWidget():
    def __init__(self, entry):
        self.html = u'<div class="issue1">'
        title = entry["title"].replace('"', '&quot;')
        self.html += u'<h2 title="'+title+'">'+title+u'</h2>'
        if "embeded" in entry and entry["embeded"]:
            self.html += '<div class="media">'
            if "image" in entry and entry["image"]:
                self.html += '<img src="'+entry["image"]+'" title="They use flash on their page!" alt="They use flash on their page!"/>'
            else:
                self.html += "<span>They use flash on their page!</span>"
            self.html += '</div>'
        elif "image" in entry and entry["image"]:
            self.html += '<div class="image"><img src="'+entry["image"]+'" alt=""/></div>'
        try: # TODO let crawler make it
            self.html += str(entry["summary"])
        except KeyError:
            try:
                self.html += str(entry["content"][0]["value"])
            except KeyError:
                log(entry)
        self.html += '<div class="small">'
        self.html += '<a href="'+entry["links"][0]["href"]+'">Source</a>'
        self.html += '<a href="about:share?url='+entry["links"][0]["href"]+'&text='+entry["title"]+'">Share</a>'
        self.html += '</div>'
        self.html += '</div>'

    def __str__(self):
        return self.html

class gtkSmallWidget(gtk.Frame):
    def __init__(self, entry):
        super(gtkSmallWidget, self).__init__()
        l = gtk.Label('<span size="x-large">'+entry["title"]+"</span>")
        l.set_use_markup(True)
        self.set_label_widget(l)

        hbox = gtk.HBox(False, 2)
        
        if entry["image"]:
            im = gtk.Image()
            im.set_from_file(entry["image"])
            hbox.pack_start(im, True, False)

        vbox = gtk.VBox(False, 1)
        hbox.pack_start(vbox, False, False)
        
        text = gtk.TextView()
        buf = gtk.TextBuffer()
        buf.set_text(entry["summary"].encode("utf-8"))
        text.set_buffer(buf)
        text.set_editable(False)
        text.set_size_request(400,-1)
        text.set_wrap_mode(gtk.WRAP_WORD_CHAR)
        text.show()
        vbox.pack_start(text, False, False)
        
        self.add(hbox)
        self.show_all()

if __name__ == "__main__":
    w = gtk.Window()
    w.add(gtkSmallWidget({
        "title": "UFO In NY!",
        "image": None,
        "summary": "300 people swear to have seen one!"+
        " Really! "}))
    w.show_all()
    w.connect("destroy", gtk.main_quit)
    gtk.main()
