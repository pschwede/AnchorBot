# -*- encoding:: utf-8 -*-

import sys
import webbrowser

from sqlalchemy.sql.expression import desc
from time import time, localtime, strftime
from flask import Flask, render_template, url_for, request, redirect, jsonify

from util.anchorbot import Anchorbot
from util.datamodel import get_session, Source, Article, Image, Keyword

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
        clickedarts = clickedarts.filter(Article.timesread < 1)
        clickedarts = clickedarts.all()  
        newarts = s.query(Article).filter(Article.date > time() - 24 * 3600)
        # TODO last-visited @UndefinedVariable 
        newarts = newarts.filter(Article.timesread < 1)
        newarts = newarts.all() 
    articles = list(set(clickedarts) | set(newarts))
    articles = sorted(articles, key=lambda x: x.date)
    for art in articles[:8]:
        art.datestr = strftime(u"%X %x", localtime(art.date))
    srclist = s.query(Source).order_by(Source.title).all()
    content = show("start", srclist, articles[:8])
    s.close()
    return content

@app.route("/_hate/id/<keyword_id>")
@app.route("/_hate/<keyword>")
def hate_key(keyword_id, keyword):
    change_key(-1, keyword_id, keyword)

@app.route("/_like/id/<keyword_id>")
@app.route("/_like/<keyword>")
def like_key(keyword_id, keyword):
    change_key(1, keyword_id, keyword)

def change_key(change, keyword_id=None, keyword=None):
    global bot
    s = get_session(bot.db)
    if keyword and not keyword_id:
        kw = s.query(Keyword).filter(Keyword.word == keyword).first()
    else:
        kw = s.query(Keyword).filter(Keyword.ID == keyword_id).first()
    if not kw:
        return "None found."
    kw.clickcount += change
    s.merge(kw)
    s.commit()
    s.close()
    return "ignored %s" % keyword


@app.route("/key/id/<keyword_id>")
@app.route("/key/<keyword>")
def read_about_key(keyword_id=None, keyword=None):
    global bot
    s = get_session(bot.db)
    if keyword and not keyword_id:
        kw = s.query(Keyword).filter(Keyword.word == keyword).first()
    else:
        kw = s.query(Keyword).filter(Keyword.ID == keyword_id).first()
    if not kw:
        return "None found."
    kw.clickcount += 1
    s.merge(kw)
    s.commit()
    arts = s.query(Article).join(Article.keywords).filter(Keyword.ID == kw.ID)
    arts = arts.order_by(desc(Article.date)).all()
    srclist = s.query(Source).order_by(Source.title).all()
    content = show("more", srclist, arts)
    for art in arts:
        art.timesread+=1
        s.merge(art)
    s.commit()
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


@app.route("/feed/id/<fid>")
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

@app.route("/redirect/<aid>")
def redirect_source(aid=None, url=None):
    global bot
    s = get_session(bot.db)
    art = s.query(Article).filter(Article.ID == aid).one()
    url = art.link
    s.close()
    return redirect(url)

@app.route("/read/<aid>")
def read_article(aid=None):
    global bot
    s = get_session(bot.db)
    arts = s.query(Article).filter(Article.ID == aid).all()
    for art in arts:
        art.timesread += 1
        s.merge(art)
    s.commit()
    srclist = s.query(Source).order_by(Source.title).all()
    content = show("more", srclist, arts)
    s.close()

def main(urls=[], cache_only=False, verbose=False, open_browser=False):
    """The main func which creates an AnchorBot
    """
    global bot, app
    bot = bot or Anchorbot(cache_only, verbose, update_event)
    map(bot.add_url, urls)
    app.run(debug=True)
    if open_browser:
        webbrowser.open("localhost:5000")


def get_cmd_options():
    usage = __file__
    return usage

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(
                sys.argv[1:] if "-a" in sys.argv else [],
                "-v" in sys.argv,  # verbose option
                "-c" in sys.argv,  # print cache only
                "-o" in sys.argv)  # open browser
    else:
        main()
