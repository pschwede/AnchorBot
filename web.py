#!/usr/bin/env python
# -*- encoding utf-8 -*-

import atexit
import argparse

from time import time
from flask import Flask, render_template, url_for, request
from flaskext.markdown import Markdown

import bot

_host = "0.0.0.0"
_port = 8000
flask_app = Flask(__name__)
Markdown(flask_app)

hashed = dict()
dehashed = dict()


@flask_app.route("/")
@flask_app.route("/gallery")
@flask_app.route("/gallery/offset/<offset>")
def gallery(offset=0, number=32, since=259200):
    offset, number, since = map(int, [offset, number, since])

    config = bot.Config(bot.CONFIGFILE)
    db = bot.initialize_database(config)
    back_then = since
    articles = db["articles"].values()
    articles = filter(lambda x: not x["read"] and x["release"] >= back_then,
                      articles)
    relevance_of_article = lambda x: sum([db["keyword_clicks"][k] for k in x["keywords"]])
    articles = sorted(articles, key=relevance_of_article, reverse=True)[offset*number:(offset + 1)*number]

    for article in articles:
        link = article["link"]
        hashed[link] = hash(link)
        dehashed[hashed[link]] = link
        print "marking as read: %s %s" % (article["read"], article["title"])
        article.update(read=True)
        db["articles"][link] = article
        print "marking as read: %s %s" % (db["articles"][link]["read"],
                                          article["title"])

    relevance = sum([relevance_of_article(x) for x in articles])

    content = render_template("gallery.html",
                              style=url_for("static", filename="default.css"),
                              articles=articles,
                              new_offset=offset + 1,
                              hashed=hashed,
                              relevance=relevance,
                              )
    return content


@flask_app.route("/feed/<url>")
@flask_app.route("/feed/id/<fid>")
@flask_app.route("/feed/id/<fid>/<amount>")
def read_feed(fid=None, url=None, amount=3):
    content = render_template("read.html",
                              style=url_for("static", filename="default.css"),
                              articles=[],
                              more_articles=[],
                              )
    return content


@flask_app.route("/like/keyword/by/id/<keyword>")
def like_keyword(keyword):
    config = bot.Config(bot.CONFIGFILE)
    db = bot.initialize_database(config)
    db["keyword_clicks"].inc(keyword)


@flask_app.route("/feeds")
@flask_app.route("/list/feeds")
def get_feeds():
    content = render_template("feeds.html",
                              style=url_for("static", filename="default.css"),
                              sources=[],
                              )
    return content


@flask_app.route("/keys")
@flask_app.route("/keywords")
@flask_app.route("/list/keys")
@flask_app.route("/list/keywords")
@flask_app.route("/list/keywords/<limit>")
def get_keywords(limit=60):
    keywords = []
    content = render_template("keywords.html",
                              style=url_for("static", filename="default.css"),
                              keywords=keywords,
                              )
    return content


@flask_app.route("/key/<keyword>")
@flask_app.route("/key/<keyword>/<amount>")
def keyword(keyword, amount=3):
    content = render_template("read.html",
                              style=url_for("static", filename="default.css"),
                              articles=[],
                              more_articles=[]
                              )
    return content


@flask_app.route("/media")
@flask_app.route("/media/<amount>")
def watch_media(amount=15):
    amount = int(amount)
    content = render_template("media.html",
                              style=url_for("static", filename="default.css"),
                              articles=[],
                              more_articles=[],
                              )
    return content


@flask_app.route("/read/<hashed>")
@flask_app.route("/read/<hashed>/because/of/<keyword>")
def read_article(hashed=None, keyword=None):
    if keyword:
        like_keyword(keyword)
    articles = list()
    more_articles = list()

    config = bot.Config(bot.CONFIGFILE)
    db = bot.initialize_database(config)
    if hashed:
        link = dehashed[int(hashed)]
        db["articles"][link]["read"] = True
        articles.append(db["articles"][link])

    more_articles = db["articles"].values()
    more_articles = filter(lambda x: keyword in x["keywords"] and not x["read"],
                           more_articles)
    relevance_of_article = lambda x: sum([db["keyword_clicks"][k] for k in x["keywords"]])
    more_articles = sorted(more_articles, key=relevance_of_article)

    content = render_template("read.html",
                              style=url_for("static", filename="default.css"),
                              articles=articles,
                              more_articles=more_articles,
                              hashed=hashed,
                              )
    return content


@flask_app.route("/quit")
def shutdown():
    request.environ.get("werkzeug.server.shutdown")()
    return "Bye"


app = argparse.ArgumentParser(description="AnchorBot server app")
app.add_argument("--host", "-u", default="0.0.0.0", type=str,
                 help="The host adress")
app.add_argument("--port", "-p", default="8000", type=int,
                 help="the port number")
app.add_argument("--debug", "-d", default=False,
                 help="run debug mode", action="store_const", const=True)
args = app.parse_args()


atexit.register(shutdown)
flask_app.run(host=args.host,
              port=args.port,
              debug=args.debug,
              use_reloader=False,
              )
