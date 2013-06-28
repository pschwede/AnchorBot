# -*- encoding: utf-8 -*-

from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, scoped_session
from sqlalchemy import create_engine, Column, Float, Integer, String, Unicode, ForeignKey
import Image as PIL
import humanize
import logging
import time
import re

Base = declarative_base()

logger = logging.getLogger("root")

class Image( Base ):
    __tablename__ = "images"

    ID = Column( Integer, primary_key=True, autoincrement=True )
    filename = Column( String, unique=True )
    cachename = Column( String )

    def __init__( self, filename, cachename=None ):
        self.filename = filename
        self.cachename = cachename

    def __repr__( self ):
        return "<%s%s>" % ( "Image", ( self.ID, self.filename, ) )

    def __cmp__( self, other ):
        im = PIL.open( self.cachename )
        a1 = im.size[0] * im.size[1]
        im = PIL.open( other.cachename )
        a2 = im.size[0] * im.size[1]
        if a1 < a2:
            return -1
        elif a1 == a2:
            return 0
        return 1

    def dictionary(self):
        return {"ID": self.ID,
                "filename": self.filename,
                "cachename": self.cachename,
                }

class Media( Base ):
    __tablename__ = "media"

    ID = Column( Integer, primary_key=True, autoincrement=True )
    filename = Column( String, unique=True )

    def __init__(self, filename):
        self.filename = filename
        self.rendered_html = self.html()

    def __repr__(self):
        return "<%s%s>" % ( "Image", ( self.ID, self.filename, ) )

    def html(self, size=(500, 225,), ratio=4./3):
        if not self.filename:
            return ''
        if "vimeo.com" in self.filename:
            vid = self.filename[10:]
            return '<iframe src="http://player.vimeo.com/video/%s" width="%i" height="%i" frameborder="0"></iframe>' % (vid, size[0], int(size[0]/ratio))
        elif "youtu.be" in self.filename:
            vid = self.filename[9:]
            return '<iframe width="%i" height="%i" src="http://www.youtube.com/embed/%s" frameborder="0" allowfullscreen></iframe>' % (size[0], int(size[0]/ratio), vid)
        elif "youtube.com/watch?v=" in self.filename:
            vid = self.filename[20:]
            return '<iframe width="%i" height="%i" src="http://www.youtube.com/embed/%s" frameborder="0" allowfullscreen></iframe>' % (size[0], int(size[0]/ratio), vid)
        elif "youtube.com/v/" in self.filename:
            vid = self.filename[14:]
            return '<iframe width="%i" height="%i" src="http://www.youtube.com/embed/%s" frameborder="0" allowfullscreen></iframe>' % (size[0], int(size[0]/ratio), vid)
        elif "youtube.com/embed/" in self.filename:
            vid = self.filename[18:]
            return '<iframe width="%i" height="%i" src="http://www.youtube.com/embed/%s" frameborder="0" allowfullscreen></iframe>' % (size[0], int(size[0]/ratio), vid)
        else:
            vid = re.findall("(?=v=)[\w-]+", self.filename)
            if vid:
                vid = vid[0]
                return '<iframe width="%i" height="%i" src="http://www.youtube.com/embed/%s" frameborder="0" allowfullscreen></iframe>' % (size[0], int(size[0]/ratio), vid)
        return ""

    def dictionary(self):
        return {"ID": self.ID,
                "filename": self.filename,
                "html": self.html(),
                }

class Source( Base ):
    __tablename__ = "sources"

    ID = Column( Integer, primary_key=True )
    link = Column( String, unique=True )
    title = Column( Unicode, default=u"" )
    image_id = Column( Integer, ForeignKey( "images.ID" ) )
    image = relationship( "Image", backref="source_br" )
    quickhash = Column( Integer, default=0 )

    def __init__( self, link, title=u"", image=None ):
        self.link = link
        self.title = title
        self.image = image

    def __repr__( self ):
        return "<%s%s>" % ( type( self ), ( self.link, self.image ) )

    def dictionary(self):
        return {"ID": self.ID,
                "link": self.link,
                "title": self.title,
                "image_id": self.image_id,
                "image": self.image and self.image.dictionary(),
                "quickhash": self.quickhash,
                }

class Page( Base ):
    __tablename__ = "pages"

    ID = Column( Integer, primary_key=True, autoincrement=True )
    name = Column( Unicode )
    date = Column( Float, nullable=False )

    def __init__( self, name, date ):
        self.name = name.decode( "utf-8" )
        self.date = date

class Article( Base ):
    __tablename__ = "articles"

    ID = Column( Integer, primary_key=True, autoincrement=True )
    date = Column( Float, nullable=False )
    title = Column( Unicode, nullable=False )
    content = Column( Unicode, nullable=False )
    link = Column( String, unique=True )
    lastread = Column( Float, default= -1 )
    timesread = Column( Integer, default=0 )
    skipcount = Column( Integer, default=0 )
    lastskip = Column( Float, default= -1)
    timestarred = Column( Float, default = -1 )
    source_id = Column( Integer, ForeignKey( "sources.ID" ), nullable=False)
    source = relationship( "Source", backref="article_br")
    image_id = Column( Integer, ForeignKey( "images.ID" ), nullable=True )
    image = relationship( "Image", backref="article_br" )
    media_id = Column( Integer, ForeignKey( "media.ID" ), nullable=True )
    media = relationship( "Media", backref="article_br" )
    page_id = Column( Integer, ForeignKey( "pages.ID" ) )
    page = relationship( "Page", backref="article_br", lazy="dynamic" )
    keywords = relationship( "Keyword", backref="article_br", lazy="dynamic", secondary="kw2arts")
    entryhash = Column( Integer, default=None )

    def __init__( self, date, title, content, link, source, image=None, keywords=None, ehash=None, media=None):
        self.date = date
        self.title = self.__unicodify(title)
        self.content = self.__unicodify(content)
        self.link = self.__unicodify(link)
        self.source = source
        self.image = image
        if keywords:
            self.set_keywords(keywords)
        if media:
            self.set_media(media)
        self.ehash = ehash
    
    def __unicodify(self, s):
        if not isinstance(s, unicode):
            try:
                return s.decode("utf-8")
            except UnicodeDecodeError:
                return ""
        return unicode(s)

    def set_keywords(self, keywords):
        for kw in keywords:
            self.keywords.append(kw)

    def set_media(self, media):
        for m in media:
            self.media.append(m)

    def set_image(self, image):
        self.image = image

    def finished(self, date):
        """Has to be called when article has been read to update statistics."""
        self.lastread = date
        self.timesread += 1

    def skipped(self, date):
        self.lastskip = date
        self.skipcount += 1

    def __repr__(self):
        return "<%s(%s)>" % ( "Article", """
        id=%s,
        title=%s,
        link=%s,
        img=%s,
        keys=%s
        """ % ( self.ID, self.title, self.link, self.image, [kw.word for kw in sorted(self.keywords, key=lambda kw: kw.clickcount)]))
    
    def dictionary(self, max_content=None):
        content_begin = self.content.rfind(self.title)
        if content_begin > 0:
            content_begin += len(self.title) + 1
        return {"ID": self.ID,
                "title": self.title, 
                "link": self.link, 
                "image": self.image and self.image.dictionary() or None, 
                "content": self.content if max_content is None else self.content[0:max_content],
                "skipcount": self.skipcount,
                "source": self.source.dictionary(),
                "timesread": self.timesread,
                "datestr": humanize.naturaltime(time.time() - self.date),
                "media": self.media and self.media.dictionary() or None,
                "keywords": [kw.dictionary() for kw in sorted(self.keywords, key=lambda kw: kw.clickcount, reverse=True)],
                }

class Keyword( Base ):
    __tablename__ = "keywords"

    ID = Column( Integer, primary_key=True )
    word = Column( Unicode, unique=True )
    clickcount = Column( Integer, default=0 )
    articles = relationship( "Article", backref="keywords_br", secondary="kw2arts" )

    def __init__( self, word, clickcount=0 ):
        if isinstance(word, str):
            self.word = word.decode( "utf-8" ).lower()
        else:
            self.word = word.lower()
        self.clickcount = clickcount

    def __repr__( self ):
        return "<%s%s>" % ( "Keyword", ( self.ID, self.word ) )

    def dictionary(self):
        return {"ID": self.ID,
                "word": self.word,
                "clickcount": self.clickcount,
                }

class Kw2art( Base ):
    __tablename__ = "kw2arts"

    kw_id = Column( Integer, ForeignKey( "keywords.ID" ), primary_key=True )
    kw = relationship( "Keyword", backref="kw2art_br")
    art_id = Column( Integer, ForeignKey( "articles.ID" ), primary_key=True )
    art = relationship( "Article", backref="kw2art_br")

    def __init__( self, kw, art ):
        self.kw = kw
        self.art = art

    def dictionary(self):
        return {"kw_id": self.kw_id,
                "kw": self.kw.dictionary(),
                "art_id": self.art_id,
                "art": self.art.dictionary(),
                }

def get_engine( filename=':memory:' ):
    """Initializes the engine, etc.
       Returns engine."""
    engine = create_engine("sqlite:///%s" % filename,
            poolclass=StaticPool,
            )
    Base.metadata.bind = engine
    Base.metadata.create_all( engine )
    return engine

def get_session( engine ):
    """Threads can get one here."""
    session = scoped_session( sessionmaker() )
    session.configure( bind=engine )
    return session

def get_session_from_new_engine(path):
    return get_session(get_engine(path))

if __name__ == "__main__":
    from sqlalchemy.exc import IntegrityError

    e = get_engine()
    session = get_session( e )
    k = Keyword( "bla" )
    session.add( k )
    session.commit()

    # after long time, without knowing, Keyword("bla") is already there
    session.add( k )
    try:
        session.commit()
    except IntegrityError, e:
        session.rollback()
        session.add( session.query( Keyword ).filter( Keyword.word == u"bla" ).first() or Keyword( "bla" ) )
        session.add( session.query( Keyword ).filter( Keyword.word == u"foo" ).first() or Keyword( "foo" ) )
        session.commit()
    session.close()
