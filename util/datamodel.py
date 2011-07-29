from sqlalchemy import Column, Integer, String, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, mapper

Base = declarative_base()

class Source(Base):
    __tablename__ = 'source'

    id = Column(Integer, primary_key=True)
    title = Column(String)
    icon = Column(Integer, ForeignKey('images.id'))
    url = Column(String)

    def __init__(self, title, icon, url):
        self.title = title
        self.icon = icon
        self.url = self.url

    def __refr__(self):
        return "<Feed('%s','%s','%s')>" % (self.title, self.icon, self.url)

class Article(Base):
    __tablename__ = 'articles'

    id = Column(Integer, primary_key=True)
    title = Column(String)
    image = Column(Integer, ForeignKey('articles.id'))
    content = Column(String)
    url = Column(String)
    date = Column(Integer)

    def __init__(self, title, image, content, url, date):
        self.title = title
        self.image = image
        self.content = content
        self.url = url
        self.date = date

    def __repr__(self):
        return "<Article('%s','%s','%s','%s')>" % (self.title, self.image, self.url, self.content)

class Image(Base):
    """Images relate to only one article"""
    __tablename__ = 'images'

    id = Column(Integer, primary_key=True)
    article = Column(Integer, ForeignKey('articles.id'))
    url = Column(String)

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
        Session = sessionmaker(bind=engine)
        self.__session = Session()
        Base.metadata.create_all(engine)

    def submit(self, thing):
        s = self.__session
        s.add(thing)
        s.commit()
    
    def submit_all(self, list_of_things):
        s = self.__session
        if list_of_things and type(list_of_things) is list:
            s.add_all(list_of_things)
        s.commit()

    def submit_image(self, url):
        s = self.__session
        s.add(Image(url))
        s.commit()
        return s.query(Image).filter(Image.url==url)[0]
    
    def submit_article(self, *ticud):
        """ticud stands for (title, image, content, url, date)"""
        s = self.__session
        s.add(Article(*ticud))
        s.commit()

if __name__ == "__main__":
    engine = create_engine("sqlite:///:memory:")
    import time
    image = Image("")
    Article("UFOS",image,"Ufos bla bla","",time.localtime())

