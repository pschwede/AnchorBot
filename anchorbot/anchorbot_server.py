import sys
from anchorbot import Anchorbot
from util.datamodel import get_session, Source, Article, Image, Keyword

from sqlalchemy.sql.expression import desc
from time import time, localtime, strftime
from flask import Flask, render_template, url_for, request
app = Flask(__name__)
bot = None # yet

def update_event(x, y):
    print "update!", x, y


def show(mode, srclist, content):
    return render_template(
            "layout.html",
            style=url_for("static", filename="default.css"),
            srclist=srclist,
            mode=mode,
            content=content
        )


@app.route("/")
def start():
    global bot
    articles = ""
    s = get_session(bot.db)
    keywords = s.query(Keyword).order_by(desc(Keyword.clickcount)).limit(10)
    for kw in set(keywords):
        clickedarts = s.query(Article).filter(Article.keywords.contains(kw))
        clickedarts = clickedarts.filter(Article.date > time() - 24 * 3600)
        # TODO last-visited
        clickedarts = clickedarts.all()  
        newarts = s.query(Article).filter(Article.date > time() - 24 * 3600)
        # TODO last-visited @UndefinedVariable 
        newarts = newarts.all() 
    articles = list(set(clickedarts) | set(newarts))
    articles = sorted(articles, key=lambda x: x.date)
    for art in articles:
        art.datestr = strftime(u"%X %x", localtime(art.date))
    srclist = s.query(Source).order_by(Source.title).all()
    content = show("start", srclist, articles)
    s.close()
    return content


@app.route("/key/<kwword>")
@app.route("/key/id=<kwid>")
def read_about_key(kwid=None, kwword=None):
    global bot
    s = get_session(bot.db)
    if kwword and not kwid:
        kw = s.query(Keyword).filter(Keyword.word == kwword).first()
    else:
        kw = s.query(Keyword).filter(Keyword.ID == kwid).first()
    if not kw:
        return "None found."
    kw.clickcount += 1
    s.merge(kw)
    s.commit()
    arts = s.query(Article).join(Article.keywords).filter(Keyword.ID == kw.ID)
    arts = arts.order_by(desc(Article.date)).all()
    srclist = s.query(Source).order_by(Source.title).all()
    content = show("more", srclist, arts)
    s.close()
    return content


@app.route("/shutdown")
def shutdown():
    try:
        request.environ.get("werkzeug.server.shutdown")()
    except:
        print "Not using werkzeug engine."
    bot.quit()
    return "bye"


@app.route("/feed/id=<fid>")
@app.route("/feed/<url>")
def read_feed(fid=None, url=None):
    global bot
    s = get_session(bot.db)
    if url:
        arts = s.query(Article).join(Article.source)
        arts = arts.filter(Source.link.contains(url)).order_by(Article.date)
        arts = arts.all()
    else:
        arts = s.query(Article).join(Article.source)
        arts = arts.filter(Source.ID == fid).order_by(desc(Article.date)).all()
    srclist = s.query(Source).order_by(Source.title).all()
    content = show("more", srclist, arts)
    s.close()
    return content


def main(urls=[], cache_only=False, verbose=False):
    """The main func which creates Lyrebird
    """
    global bot, app
    bot = bot or Anchorbot(True, cache_only, verbose, update_event)
    map(bot.add_url, urls)
    app.run(debug=True)


def get_cmd_options():
    usage = __file__
    return usage

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(
                sys.argv[1:] if "-a" in sys.argv else [],
                "-v" in sys.argv,  # verbose option
                "-c" in sys.argv)  # print cache only
    else:
        main()
