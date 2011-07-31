# -*- encoding; utf-8 -*-

from sqlalchemy import Column, Integer, Float, String, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.expression import desc
from sqlalchemy.orm import sessionmaker, mapper
from sqlalchemy.exc import IntegrityError
import sys
#TODO use Logger class for outputs

Base = declarative_base()

class Source(Base):
    __tablename__ = 'sources'

    id = Column(Integer, primary_key=True)
    title = Column(String)
    icon = Column(Integer, ForeignKey('images.id'))
    url = Column(String, unique=True, nullable=False)
    h = Column(Integer)

    def __init__(self, title, icon, url, h):
        self.title = title
        self.icon = icon
        self.url = self.url
        self.h = h

    def __refr__(self):
        return "<Feed('%s','%s','%s', '%s')>" % (self.title, self.icon, self.url, h)

class Article(Base):
    __tablename__ = 'articles'

    id = Column(Integer, primary_key=True)
    title = Column(String, default=u'')
    image = Column(Integer, ForeignKey('articles.url'), nullable=True, default=u'')
    content = Column(String, default=u'')
    url = Column(String, unique=True, nullable=False)
    source_url = Column(String, ForeignKey('sources.url'), nullable=False)
    date = Column(Float)

    def __init__(self, title, image, content, url, source_url, date):
        self.title = title
        self.image = image
        self.content = content
        self.url = url
        self.source_url = source_url
        self.date = date

    def to_dict(self):
        return {"title":    self.title,
                "image":    self.image,
                "content":  self.content,
                "link":      self.url,
                "source_url":   self.source_url,
                "date":     self.date,
                }

    def __repr__(self):
        return "<Article('%s','%s','%s','%s')>" % (self.title, self.image, self.url, self.content)

class Image(Base):
    """Images relate to only one article"""
    __tablename__ = 'images'

    id = Column(Integer, primary_key=True)
    url = Column(String, unique=True, nullable=False, default=u'')

    def __init__(self, url):
        self.url = url

    def __repr__(self):
        return "<Image('%s')>" % self.url

class DataModel:
    def __init__(self, filename=None):
        if filename:
            print "Using %s database for engine" % filename
            self.__engine = engine = create_engine("sqlite:///%s" % filename)
        else:
            print "No filename given. Setting up temporary sqlalchemy engine to /:memory:"
            self.__engine = engine = create_engine("sqlite:///:memory:", echo=True)

        # ugly unicode accept hack from stackoverflow.com:
        self.__engine.raw_connection().connection.text_factory = str

        self.sessionmaker = sessionmaker(bind=engine)
        Base.metadata.create_all(engine, checkfirst=True)

    def submit(self, thing):
        s = self.sessionmaker()
        s.add(thing)
        s.commit()
    
    def submit_all(self, list_of_things):
        s = self.sessionmaker()
        l = list_of_things
        s.add_all(l)
        try:
            s.commit()
        except IntegrityError, e:
            s.rollback()
            for i in l:
                try:
                    if i not in s:
                        s.add(i)
                        s.commit()
                except IntegrityError, e:
                    s.rollback()

    def submit_image(self, url):
        s = self.sessionmaker()
        s.add(Image(url))
        s.commit()
        return s.query(Image).filter(Image.url==url)[0]
    
    def submit_article(self, title, content, url, date, image_uri):
        s = self.sessionmaker()
        s.add(Article(title, content, url, date))
        s.add(Image(image))
        s.commit()

    def submit_source(self, title, icon, url, h):
        s = self.sessionmaker()
        s.add(Source(title, icon, url, h))
        try:
            s.commit()
        except IntegrityError:
            s.rollback()
            #TODO try updating

    def has_article(self, url):
        s = self.sessionmaker()
        return 0 < s.query(Article).filter(Article.url == url).count()

    def has_image(self, url):
        s = self.sessionmaker()
        return 0 < s.query(Image).filter(Image.url == url).count()

    def get_articles(self, source_url, time_back=0, number=0, offset=0):
        s = self.sessionmaker()
        if time_back>0:
            return [a.to_dict() for a in s.query(Article).filter(
                    Article.source_url == source_url
                ).filter(
                    Article.date >= time_back
                ).order_by(
                    desc(Article.date)
                )[offset:number]
                ]
        else:
            return [a.to_dict() for a in s.query(Article).filter(
                        Article.source_url == source_url
                        )[offset:number]
                        ]

if __name__ == "__main__":
    engine = create_engine("sqlite:///:memory:")
    import time
    image = Image("")
    Article(u"UFOS",u"",u"x\dfUfos bla bla",u"",0)#time.time())

