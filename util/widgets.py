import gtk, pango

class SmallWidget(gtk.Frame):
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
