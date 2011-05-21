import gtk, pango
from logger import log
from util import _

class tweet_window( gtk.Dialog ):
    def __init__( self, service=None, user=None, password=None, text=None ):
        super( tweet_window, self ).__init__()
        self.user, self.__password = user, password
        self.service = service

        table = gtk.Table()
        self.vbox.pack_start( table )

        self.serv_label = gtk.Label( service )
        table.attach( self.serv_label, 0,2,0,1 )

        self.user_label = gtk.Label( "Name:" )
        table.attach( self.user_label, 0,1,1,2 )
        self.user_entry = gtk.Entry()
        table.attach( self.user_entry, 1,2,1,2 )

        self.user_label = gtk.Label( "Password:" )
        table.attach( self.user_label, 0,1,2,3 )
        self.user_password = gtk.Entry()
        self.user_password.set_visibility( False )
        table.attach( self.user_password, 1,2,2,3 )

        scrolled = gtk.ScrolledWindow()
        self.text_buf = gtk.TextBuffer()
        self.text_buf.set_text( text )
        textv = gtk.TextView( self.text_buf )
        textv.set_wrap_mode( gtk.WRAP_WORD_CHAR )
        scrolled.add( textv )
        table.attach( scrolled, 0,2,3,4 )

        table.show_all()
        self.add_button( gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL )
        self.add_button( gtk.STOCK_YES, gtk.RESPONSE_OK )

    def run( self ):
        resp = super( tweet_window, self ).run()
        if resp == gtk.RESPONSE_OK:
            self.hide()
            return ( self.user_entry.get_text(), 
                    self.user_password.get_text(), 
                    self.text_buf.get_text( self.text_buf.get_start_iter(), self.text_buf.get_end_iter() ), )
        else:
            self.hide()
            return None

class main_window( gtk.Window ):
    def __init__( self, info, controller ):
        super( gtk.Window, self ).__init__()
        self.ctrl = controller
        self.info = info
        self.set_title( self.info["__appname__"] + " " + self.info["__version__"] )
        self.connect( "destroy", self.ctrl.quit )

        #vbox = self.vbox = gtk.VBox( False, 0 )
        vbox = gtk.VBox()
        #vbox.pack_start( hbox, True, True )

        # BEGIN toolbar

        toolbar = gtk.Toolbar()
        toolbar.set_border_width( 0 )
        vbox.pack_start( toolbar, False, True )

        new_tool = gtk.ToolButton( gtk.STOCK_ADD )
        new_tool.connect( "clicked", lambda w: self.new_feed_dialog() )
        toolbar.add( new_tool )

        show_tool = gtk.ToolButton( gtk.STOCK_REFRESH )
        show_tool.connect( "clicked", lambda w: self.ctrl.download_all() )
        toolbar.add( show_tool )

        conf_tool = gtk.ToolButton( gtk.STOCK_PREFERENCES )
        # connect conf_tool
        toolbar.add( conf_tool )

        about_tool = gtk.ToolButton( gtk.STOCK_ABOUT )
        about_tool.connect( "clicked", self.show_about )
        toolbar.add( about_tool )

        sep_tool = gtk.SeparatorToolItem()
        sep_tool.set_expand( True )
        toolbar.add( sep_tool )

        quit_tool = gtk.ToolButton( gtk.STOCK_QUIT )
        quit_tool.connect( "clicked", self.ctrl.quit )
        toolbar.add( quit_tool )

        # END toolbar

        hpaned = gtk.HPaned()
        vbox.pack_start( hpaned, True, True )

        # BEGIN self.groups

        self.groups = gtk.TreeView()
        self.groups.connect( "cursor_changed", self._cell_clicked )

        groups_model = gtk.TreeStore( str, str )
        self.treedic = {}
        self.treedic["Feeds"] = groups_model.append( None, [_( "Feeds" ), None] )
        self.groups.set_model( groups_model )

        cat_cell = gtk.CellRendererText()
        cat_column = gtk.TreeViewColumn( _( 'Category' ) )
        cat_column.pack_start( cat_cell, True )
        cat_column.add_attribute( cat_cell, 'text', 0 )
        self.groups.append_column( cat_column )

        itm_cell = gtk.CellRendererText()
        itm_column = gtk.TreeViewColumn( _( 'Item' ) )
        itm_column.pack_start( itm_cell, True )
        itm_column.add_attribute( itm_cell, 'text', 1 )
        self.groups.append_column( itm_column )

        scroller = gtk.ScrolledWindow()
        scroller.add_with_viewport( self.groups )
        hpaned.pack1( scroller )

        # END self.groups

        
        hpaned.pack2( self.ctrl.browser )
        hpaned.set_position( 0 )
        
        self.status = gtk.Statusbar()
        vbox.pack_start( self.status, False, True )

        self.add( vbox )
        self.show_all()

    def _cell_clicked( self, view ):
        sel = view.get_selection()
        model, piter = sel.get_selected()
        if piter:
            url = model.get_value( piter, 1 )
            if url:
                self.ctrl.show( url )

    def new_feed_dialog( self ):
        w = gtk.Window( gtk.WINDOW_POPUP )

        table = gtk.Table( 2,2 )
        table.set_row_spacings( 3 )
        table.set_col_spacings( 3 )
        table.set_border_width( 3 )
        w.add( table )
        
        url_label = gtk.Label( _( "URL:" ) )
        table.attach( url_label, 0, 1, 0, 1 )

        url_entry = gtk.Entry()
        table.attach( url_entry, 1, 2, 0, 1 )
        url_entry.set_property("has-focus", True)

        hbox = gtk.HBox( True )
        table.attach( hbox, 0, 2, 1, 2 )

        ok = gtk.Button( stock=gtk.STOCK_OK )
        ok.connect( "clicked", lambda x: ( self.ctrl.add_url( url_entry.get_text() ), w.destroy() ) )
        hbox.pack_end( ok, False, False )
        ok.set_property("has-default", True)

        cancel = gtk.Button( stock=gtk.STOCK_CANCEL )
        cancel.connect( "clicked", lambda x: w.destroy() )
        hbox.pack_end( cancel, False, False )

        w.show_all()

    def show_about( self, stuff=None ):
        ad = gtk.AboutDialog()
        ad.set_program_name( self.info["__appname__"] )
        ad.set_version( self.info["__version__"] )
        ad.set_authors( [self.info["__author__"]] )
        ad.set_copyright( self.info["__author__"] )
        ad.run()
        ad.destroy()


class htmlSmallWidget():
    def __init__( self, entry ):
        self.html = u'<div class="issue1">'
        title = entry["title"].replace( '"', '&quot;' )
        self.html += u'<h2 title="' + title + '">' + title + u'</h2>'
        if "embeded" in entry and entry["embeded"]:
            self.html += '<div class="media">'
            if "image" in entry and entry["image"]:
                self.html += '<img src="' + entry["image"] + '" title="They use flash on their page!" alt="They use flash on their page!"/>'
            else:
                self.html += "<span>They use flash on their page!</span>"
            self.html += '</div>'
        elif "image" in entry and entry["image"]:
            self.html += '<div class="image"><img src="' + entry["image"] + '" alt=""/></div>'
        try: # TODO let crawler make it
            self.html += str( entry["summary"] )
        except KeyError:
            try:
                self.html += str( entry["content"][0]["value"] )
            except KeyError:
                pass
                # log( "couldn't find [content[0][value] in " + title ) #log( entry )
        self.html += '<div class="small">'
        try:
            self.html += '<a href="' + entry["links"][0]["href"] + '">Source</a>'
            self.html += '<a href="about:share?url=' + entry["links"][0]["href"] + '&text=' + entry["title"] + '">Share</a>'
        except KeyError:
            pass
            # log( "coudln't find [links][0][href] in " + title ) #log( entry )
        self.html += '</div>'
        self.html += '</div>'

    def __str__( self ):
        return self.html

class gtkSmallWidget( gtk.Frame ):
    def __init__( self, entry ):
        super( gtkSmallWidget, self ).__init__()
        l = gtk.Label( '<span size="x-large">' + entry["title"] + "</span>" )
        l.set_use_markup( True )
        self.set_label_widget( l )

        hbox = gtk.HBox( False, 2 )
        
        if entry["image"]:
            im = gtk.Image()
            im.set_from_file( entry["image"] )
            hbox.pack_start( im, True, False )

        vbox = gtk.VBox( False, 1 )
        hbox.pack_start( vbox, False, False )
        
        text = gtk.TextView()
        buf = gtk.TextBuffer()
        buf.set_text( entry["summary"].encode( "utf-8" ) )
        text.set_buffer( buf )
        text.set_editable( False )
        text.set_size_request( 400,-1 )
        text.set_wrap_mode( gtk.WRAP_WORD_CHAR )
        text.show()
        vbox.pack_start( text, False, False )
        
        self.add( hbox )
        self.show_all()

if __name__ == "__main__":
    w = gtk.Window()
    w.add( gtkSmallWidget( {
        "title": "UFO In NY!",
        "image": None,
        "summary": "300 people swear to have seen one!" + 
        " Really! "} ) )
    w.show_all()
    w.connect( "destroy", gtk.main_quit )
    gtk.main()
