# -*- encoding: utf-8 -*-

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, scoped_session
from sqlalchemy import create_engine, Column, Float, Integer, String, Unicode, ForeignKey
import Image as PIL

Base = declarative_base()

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
        im = PIL.open( self.cache[self.filename] )
        a1 = int.__mul__( im.size )
        im = PIL.open( self.cache[other.filename] )
        a2 = int.__mul__( im.size )
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
                "image": self.mage.dictionary(),
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
    source_id = Column( Integer, ForeignKey( "sources.ID" ), nullable=False )
    source = relationship( "Source", backref="article_br" )
    image_id = Column( Integer, ForeignKey( "images.ID" ), nullable=True )
    image = relationship( "Image", backref="article_br" )
    page_id = Column( Integer, ForeignKey( "pages.ID" ) )
    page = relationship( "Page", backref="article_br", lazy="dynamic" )
    keywords = relationship( "Keyword", backref="article_br", lazy="dynamic", secondary="kw2arts" )
    entryhash = Column( Integer, default=None )

    def __init__( self, date, title, content, link, source, image=None, keywords=None, ehash=None ):
        self.date = date
        self.title = self.__unicodify(title)
        self.content = self.__unicodify(content)
        self.link = self.__unicodify(link)
        self.source = source
        self.image = image
        if keywords:
            self.set_keywords( keywords )
        self.ehash = ehash
    
    def __unicodify(self, s):
        if not isinstance(s, unicode):
            return s.decode("utf-8")
        return s

    def set_keywords( self, keywords ):
        for kw in keywords:
            self.keywords.append( kw )

    def set_image( self, image ):
        self.image = image

    def finished( self, date ):
        """Has to be called when article has been read to update statistics."""
        self.lastread = date
        self.timesread += 1

    def __repr__( self ):
        return "<%s(%s)>" % ( "Article", """
        id=%s,
        title=%s,
        link=%s,
        img=%s,
        keys=%s
        """ % ( self.ID, self.title, self.link, self.image, [kw.word for kw in sorted(self.keywords, key=lambda kw: kw.clickcount)]))
    
    def dictionary(self):
        return {"ID": self.ID,
                "title": self.title, 
                "link": self.link, 
                "image": self.image.dictionary(), 
                "keywords": [kw.dictionary() for kw in sorted(self.keywords, key=lambda kw: kw.clickcount)],
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
                "clickcounts": self.clickcount,
                }

class Kw2art( Base ):
    __tablename__ = "kw2arts"

    kw_id = Column( Integer, ForeignKey( "keywords.ID" ), primary_key=True )
    kw = relationship( "Keyword", backref="kw2art_br" )
    art_id = Column( Integer, ForeignKey( "articles.ID" ), primary_key=True )
    art = relationship( "Article", backref="kw2art_br" )

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
    engine = create_engine( "sqlite:///%s" % filename )
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
        #print [session.query(Keyword).filter(Keyword.word == kw).first() or Keyword(kw) for kw in ["bla", "foo"]]
        #session.add(a)
        session.add( session.query( Keyword ).filter( Keyword.word == u"bla" ).first() or Keyword( "bla" ) )
        session.add( session.query( Keyword ).filter( Keyword.word == u"foo" ).first() or Keyword( "foo" ) )
        session.commit()
