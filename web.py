#!/usr/bin/env python
# -*- encoding utf-8 -*-

"""News display server."""

from re import compile as re_compile
import sys
import argparse
import markdown

from flask import Flask, render_template, url_for
from flaskext.markdown import Markdown

import bot

_HOST = "0.0.0.0"
_PORT = 8000
FLASK_APP = Flask(__name__)
Markdown(FLASK_APP)

HASHED = dict()
DEHASHED = dict()


def __get_source_domain(uri):
    if uri.startswith('http'):
        print uri.split('/')
        return uri.split('/')[2]
    return uri


def __relevance_of_keyword(database, keyword):
    """Retrieve relevance factor of a keyword."""
    return database["keyword_clicks"][keyword[0]]


def __relevance_of_article(database, article):
    """Retrieve relevance factor of an article."""
    return sum([(database["keyword_clicks"][k] or 0)
                for k in article["keywords"]])


@FLASK_APP.route("/")
@FLASK_APP.route("/gallery")
@FLASK_APP.route("/gallery/keyword/<keyword>")
@FLASK_APP.route("/gallery/offset/<offset>")
def gallery(offset=0, number=32, since=259200, keyword=None):
    """Arrangement of unread articles."""
    offset = int(offset)
    number = int(number)
    back_then = int(since)

    unread_young = lambda x: not x["read"] and x["release"] >= back_then
    relevance_of_article = lambda x: __relevance_of_article(database, x)
    articles = list()

    config = bot.Config(bot.CONFIGFILE)
    database = bot.initialize_database(config)

    # look for yound, unread articles
    articles = []
    for article in database["articles"].values():
        if not unread_young(article):
            continue
        articles.append(article)

    # sort by relevance and cut off slice
    articles = sorted(articles,
                      key=relevance_of_article,
                      reverse=True)[offset*number:(offset*number+number)]

    # mark article as read and update database
    for article in articles:
        link = article["link"]

        HASHED[link] = hash(link)
        DEHASHED[HASHED[link]] = link

        article.update(read=True)
        print article

        database["articles"][link] = article

    # prepare data sets for gallery
    scores = {a["link"]: relevance_of_article(a) for a in articles}
    scores["all"] = sum([relevance_of_article(x) for x in articles])
    content = render_template("gallery.html",
                              style=url_for("static", filename="default.css"),
                              articles=articles,
                              new_offset=offset + 1,
                              hashed=HASHED,
                              scores=scores)
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
def get_keywords(number=100, offset=0):
    config = bot.Config(bot.CONFIGFILE)
    database = bot.initialize_database(config)
    keywords = database["keyword_clicks"].items()
    relevance_of_keyword = lambda x: __relevance_of_keyword(database, x)
    keywords = sorted(keywords,
                      key=relevance_of_keyword,
                      reverse=True)[offset*number:(offset+1)*number]
    content = render_template("keywords.html",
                              style=url_for("static", filename="default.css"),
                              number=number,
                              offset=offset,
                              keywords=keywords)
    return content


@FLASK_APP.route("/key/<keyword>")
@FLASK_APP.route("/key/<keyword>/<amount>")
def read_keyword(keyword, amount=3):
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
    hashed = int(hashed)
    if keyword:
        like_keyword(keyword)

    articles = list()
    more_articles = list()

    config = bot.Config(bot.CONFIGFILE)
    database = bot.initialize_database(config)
    if hashed:
        link = None
        try:
            link = DEHASHED[hashed]
        except KeyError:
            for article in database["articles"]:
                if hashed == hash(article):
                    link = article
                    break
        if link:
            database["articles"][link]["read"] = True
            article = dict(database["articles"][link])
            article['source'] = __get_source_domain(link)
            article['date'] = time.ctime(article['release'])
            articles.append(article)

    unread_with_keyword = lambda x: not x["read"] and keyword in x["keywords"]
    relevance_of_article = lambda x: __relevance_of_article(database, x)
    more_articles = sorted([x for x in database["articles"].values()
                            if unread_with_keyword(x)],
                           key=relevance_of_article)
    HASHED.update({x["link"]: hash(x["link"]) for x in more_articles})

    return render_template("read.html",
                           style=url_for("static", filename="default.css"),
                           articles=articles,
                           more_articles=more_articles,
                           hashed=HASHED,
                           keyword=keyword)


def __main():
    """Main"""
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
    except KeyboardInterrupt, e:
        sys.exit(0)

if __name__ == "__main__":
    __main()
