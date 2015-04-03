#!/usr/bin/env python
# -*- encoding utf-8 -*-

import atexit
import argparse

from flask import Flask, render_template, url_for, request
from flaskext.markdown import Markdown

import bot

_HOST = "0.0.0.0"
_PORT = 8000
FLASK_APP = Flask(__name__)
Markdown(FLASK_APP)

HASHED = dict()
DEHASHED = dict()


def __relevance_of_keyword(database, keyword):
    return database["keyword_clicks"][keyword[0]]


def __relevance_of_article(database, article):
    return sum([database["keyword_clicks"][k] for k in article["keywords"]])


@FLASK_APP.route("/")
@FLASK_APP.route("/gallery")
@FLASK_APP.route("/gallery/keyword/<keyword>")
@FLASK_APP.route("/gallery/offset/<offset>")
def gallery(offset=0, number=32, since=259200, keyword=None):
    offset, number, since = [int(x) for x in [offset, number, since]]

    config = bot.Config(bot.CONFIGFILE)
    database = bot.initialize_database(config)
    back_then = since
    articles = database["articles"].values()
    unread_young = lambda x: not x["read"] and x["release"] >= back_then
    articles = [x for x in articles if unread_young(x)]
    relevance_of_article = lambda x: __relevance_of_article(database, x)
    articles = sorted(articles,
                      key=relevance_of_article,
                      reverse=True)[offset*number:(offset + 1)*number]

    for article in articles:
        link = article["link"]
        HASHED[link] = hash(link)
        DEHASHED[HASHED[link]] = link
        print "marking as read: %s %s" % (article["read"], article["title"])
        article.update(read=True)
        database["articles"][link] = article

    relevance = sum([relevance_of_article(x) for x in articles])

    content = render_template("gallery.html",
                              style=url_for("static", filename="default.css"),
                              articles=articles,
                              new_offset=offset + 1,
                              hashed=HASHED,
                              relevance=relevance)
    return content


@FLASK_APP.route("/feed/<url>")
@FLASK_APP.route("/feed/id/<fid>")
@FLASK_APP.route("/feed/id/<fid>/<amount>")
def read_feed():
    content = render_template("read.html",
                              style=url_for("static", filename="default.css"),
                              articles=[],
                              more_articles=[])
    return content


@FLASK_APP.route("/like/keyword/by/id/<keyword>")
def like_keyword(keyword):
    config = bot.Config(bot.CONFIGFILE)
    database = bot.initialize_database(config)
    database["keyword_clicks"].inc(keyword)


@FLASK_APP.route("/feeds")
@FLASK_APP.route("/list/feeds")
def get_feeds():
    content = render_template("feeds.html",
                              style=url_for("static", filename="default.css"),
                              sources=[])
    return content


@FLASK_APP.route("/keys")
@FLASK_APP.route("/keywords")
@FLASK_APP.route("/list/keys")
@FLASK_APP.route("/list/keywords")
@FLASK_APP.route("/list/keywords/offset/<offset>")
def get_keywords(number=60, offset=0):
    config = bot.Config(bot.CONFIGFILE)
    database = bot.initialize_database(config)
    keywords = database["keyword_clicks"].items()
    relevance_of_keyword = lambda x: __relevance_of_keyword(database, x)
    keywords = sorted(keywords, key=relevance_of_keyword, reverse=True)[offset*number:(offset+1)*number]
    content = render_template("keywords.html",
                              style=url_for("static", filename="default.css"),
                              keywords=keywords)
    return content


@FLASK_APP.route("/key/<keyword>")
@FLASK_APP.route("/key/<keyword>/<amount>")
def keyword(keyword, amount=3):
    content = render_template("read.html",
                              style=url_for("static", filename="default.css"),
                              articles=[],
                              more_articles=[])
    return content


@FLASK_APP.route("/media")
@FLASK_APP.route("/media/<amount>")
def watch_media(amount=15):
    amount = int(amount)
    content = render_template("media.html",
                              style=url_for("static", filename="default.css"),
                              articles=[],
                              more_articles=[])
    return content


@FLASK_APP.route("/read/<hashed>")
@FLASK_APP.route("/read/<hashed>/because/of/<keyword>")
def read_article(hashed=None, keyword=None):
    if keyword:
        like_keyword(keyword)
    articles = list()
    more_articles = list()

    config = bot.Config(bot.CONFIGFILE)
    database = bot.initialize_database(config)
    if hashed:
        link = DEHASHED[int(hashed)]
        database["articles"][link]["read"] = True
        articles.append(database["articles"][link])

    more_articles = database["articles"].values()
    unread_with_keyword = lambda x: keyword in x["keywords"] and not x["read"]
    more_articles = [x for x in more_articles if unread_with_keyword(x)]
    relevance_of_article = lambda x: __relevance_of_article(database, x)
    more_articles = sorted(more_articles, key=relevance_of_article)

    content = render_template("read.html",
                              style=url_for("static", filename="default.css"),
                              articles=articles,
                              more_articles=more_articles,
                              hashed=HASHED)
    return content


if __name__ == "__main__":
    APP = argparse.ArgumentParser(description="AnchorBot server app")
    APP.add_argument("--host", "-u", default="0.0.0.0", type=str,
                     help="The host adress")
    APP.add_argument("--port", "-p", default="8000", type=int,
                     help="the port number")
    APP.add_argument("--debug", "-d", default=False,
                     help="run debug mode", action="store_const", const=True)
    ARGS = APP.parse_args()

    try:
        FLASK_APP.run(host=ARGS.host,
                      port=ARGS.port,
                      debug=ARGS.debug,
                      use_reloader=False)
    except RuntimeError, e:
        print e
