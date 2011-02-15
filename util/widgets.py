import gtk, pango
from logger import log

class htmlSmallWidget():
    def __init__(self, entry):
        self.html = str()
        self.html += '<div class="issue1">'
        self.html += '<h2>'+str(entry["title"])+'</h2>'
        try: # TODO let crawler make it
            self.html += str(entry["summary"])
        except KeyError:
            try:
                self.html += str(entry["content"][0]["value"])
            except KeyError:
                log(entry)
        self.html += '<div class="small">'
        self.html += '<a href="'+entry["links"][0]["href"]+'">Source</a>'
        self.html += '<a href="http://twitter.com/share?url='+entry["links"][0]["href"]+'&text='+entry["title"]+'">Tweet</a>'
        self.html += '</div>'
        self.html += '</div>'

    def __str__(self):
        return self.html

class gtkSmallWidget(gtk.Frame):
    def __init__(self, entry):
        super(SmallWidget, self).__init__()
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
    w.add(SmallWidget({
        "title": "UFO In NY!",
        "image": None,
        "summary": "300 people swear to have seen one!"+
        " Really! "}))
    w.show_all()
    w.connect("destroy", gtk.main_quit)
    gtk.main()
