from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
class Article(Base):
    __tablename__ = 'articles'

    id = Column(Integer, primary_key=True)
    title = Column(String)
    image = Column(String)
    content = Column(String)
    date = Column(Integer)

    def __init__(self, title, image, content, date):
        self.title = title
        self.image = image
        self.content = content
        self.date = date

    def __repr__(self):
        return "<Article('%s','%s','%s')>" % (self.title, self.image, self.content)

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

if __name__ == "__main__":
    engine = Engine("sqlite:///:memory:")
    from date import date,now
    Article("UFOS",None,"Ufos bla bla",date.now())

