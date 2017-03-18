#!/usr/bin/env python2
# -*- encoding utf-8 -*-

"""News display server."""

from re import compile as re_compile, sub as re_sub, IGNORECASE
import sys
#via http://stackoverflow.com/a/14919377
reload(sys)
sys.setdefaultencoding('utf-8')

import time
import argparse
import markdown

from flask import Flask, render_template, url_for, escape
from flaskext.markdown import Markdown

from bot import Bot

_HOST = "0.0.0.0"
_PORT = 8000
FLASK_APP = Flask(__name__)
Markdown(FLASK_APP)

HASHED = dict()
DEHASHED = dict()

RE_SENTENCES = re_compile(r"[\(]?.+?[\.!\?][\)]?(?!\S)")
RE_PARAGRAPHS = re_compile(r"(?<=<p>)[^<]+(?=</p>)")


def __get_source_domain(uri):
    if uri.startswith('http'):
        return uri.split('/')[2]
    return uri


@FLASK_APP.route("/table")
def table(offset=0, number=12, since=259200, keyword=None):
    """Table arrangement of unread articles."""
    global HASHED, DEHASHED
    offset = int(offset)
    number = int(number)
    back_then = int(since)

    HASHED = dict()
    DEHASHED = dict()

    watched_keywords_art = dict()

    with Bot() as b:
        articles = b.hot_articles(offset, number, since, keyword)
        watched_keywords = frozenset(b.database["keyword_clicks"].keys())
        for article in articles:
            link = article["link"]

            if not article["keywords"]:
                b.update_article(link, read=True)
                continue

            # generate and remember hash values
            HASHED[link] = hash(link)
            DEHASHED[hash(link)] = link

            # split headline into links
            split_headline = unicode(escape(article["title"].lower())).split(" ")
            sorted_kwords = sorted(article["keywords"], key=len, reverse=True)
            linked_headline = []
            contained_watched_keywords = watched_keywords & set(sorted_kwords)
            watched_keywords_art[article["link"]] = contained_watched_keywords
            for word in split_headline:
                kwords = [kw for kw in sorted_kwords if kw.lower() in word.lower()]
                if not kwords:
                    continue

                template = r"""<a href="/read/%s/because/of/\1" target="_blank">\1</a>"""
                if word in contained_watched_keywords:
                    template = "<i>%s</i>" % template

                linked_headline.append(
                        re_sub(r"(%s)" % kwords[0],
                               template % HASHED[link],
                               word,
                               flags=IGNORECASE))
            if not linked_headline:
                continue
            article["linked_headline"] = " ".join(linked_headline)

        [int(k) for k in HASHED.values()]

        # prepare data sets for gallery
        scores = {a["link"]: b.relevance_of_article(a) for a in articles}
        scores["all"] = sum([b.relevance_of_article(x) for x in articles])
        content = render_template("table.html",
                                  style=url_for("static", filename="default.css"),
                                  articles=articles,
                                  new_offset=offset + 1,
                                  wka=watched_keywords_art,
                                  hashed=HASHED,
                                  scores=scores)
        return content



@FLASK_APP.route("/")
@FLASK_APP.route("/gallery")
@FLASK_APP.route("/gallery/keyword/<keyword>")
@FLASK_APP.route("/gallery/offset/<offset>")
def gallery(offset=0, number=12, since=259200, keyword=None):
    """Arrangement of unread articles."""
    global HASHED, DEHASHED
    offset = int(offset)
    number = int(number)
    back_then = int(since)

    HASHED = dict()
    DEHASHED = dict()

    with Bot() as b:
        articles = b.hot_articles(offset, number, since, keyword)
        watched_keywords = frozenset(b.database["keyword_clicks"].keys())
        for article in articles:
            link = article["link"]

            if not article["keywords"]:
                b.update_article(link, read=True)
                continue

            # generate and remember hash values
            HASHED[link] = hash(link)
            DEHASHED[hash(link)] = link

            # split headline into links
            split_headline = unicode(escape(article["title"].lower())).split(" ")
            sorted_kwords = sorted(article["keywords"], key=len, reverse=True)
            linked_headline = []
            contained_watched_keywords = watched_keywords & set(sorted_kwords)
            for word in split_headline:
                kwords = [kw for kw in sorted_kwords if kw.lower() in word.lower()]
                if not kwords:
                    continue

                template = r"""<a href="/read/%s/because/of/\1" target="_blank">\1</a>"""
                if word in contained_watched_keywords:
                    template = "<i>%s</i>" % template

                linked_headline.append(
                        re_sub(r"(%s)" % kwords[0],
                               template % HASHED[link],
                               word,
                               flags=IGNORECASE))
            if not linked_headline:
                continue
            article["linked_headline"] = " ".join(linked_headline)

        [int(k) for k in HASHED.values()]

        # prepare data sets for gallery
        scores = {a["link"]: b.relevance_of_article(a) for a in articles}
        scores["all"] = sum([b.relevance_of_article(x) for x in articles])
        content = render_template("gallery.html",
                                  style=url_for("static", filename="default.css"),
                                  articles=articles,
                                  new_offset=offset + 1,
                                  hashed=HASHED,
                                  scores=scores)
        return content


@FLASK_APP.route("/mark/as/read/<hashed>")
def mark_as_read(hashed):
    global DEHASHED

    with Bot() as b:
        hashed = [int(h) for h in hashed.split("+")]
        for h in hashed:
            try:
                link = DEHASHED[h]
                if link:
                    b.update_article(link, read=True)
            except KeyError, e:
                print e, "not in", DEHASHED
        return "OK"


@FLASK_APP.route("/dismiss/<hashed>")
def dismiss(hashed):
    mark_as_read(hashed)
    return gallery()


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
    with Bot() as b:
        b.database["keyword_clicks"].update([keyword])


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
    with Bot() as b:
        keywords = b.database["keyword_clicks"].items()
        keywords = sorted(keywords,
                          key=b.relevance_of_keyword,
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
@FLASK_APP.route("/video")
@FLASK_APP.route("/video/<amount>")
def watch_media(amount=15):
    amount = int(amount)
    with Bot() as b:
        articles = list()
        for article in b.hot_articles(number=None, since=0):
            if amount <= 0:
                break
            if article["media"]:
                articles.append(article)
            amount -= 1

        return render_template("media.html",
                               style=url_for("static", filename="default.css"),
                               articles=articles,
                               more_articles=[])


@FLASK_APP.route("/read/<hashed>")
@FLASK_APP.route("/read/<hashed>/because/of/<keyword>")
def read_article(hashed=None, keyword=None):
    global HASHED

    hashed = int(hashed)
    if keyword:
        like_keyword(keyword)

    articles = list()
    more_articles = list()

    with Bot() as b:
        if hashed:
            link = None
            try:
                link = DEHASHED[hashed]
            except KeyError:
                for article in b.database["articles"]:
                    if hashed == hash(article):
                        link = article
                        break
            if link:
                b.update_article(link, read=True)

                article = dict(b.database["articles"][link])
                article['source'] = __get_source_domain(link)
                article['date'] = time.ctime(article['release'])

                original_content = markdown.markdown(escape(article['content']))
                spaned_content = []
                for paragraph in [p for p in RE_PARAGRAPHS.findall(original_content) if p]:
                    sentences = [s for s in RE_SENTENCES.findall(paragraph) if s]
                    if not sentences:
                        continue
                    elif len(sentences) == 1:
                        spaned_content.append("<p><span>%s</span></p>" % sentences[0])
                    else:
                        spaned_content.append(
                                "<p>%s</p>" % \
                                ("<span>%s</span>"*3 % \
                                (sentences[0], "".join(sentences[1:-2]), sentences[-1]))
                                )
                article['spaned_content'] = " ".join(spaned_content)
                if keyword:
                    article['spaned_content'] = re_sub(r"(%s)" % keyword,
                            r"<strong>\1</strong>", article['spaned_content'],
                            flags=IGNORECASE)
                articles.append(article)

        unread_with_keyword = lambda x: not x["read"] and keyword in x["keywords"]
        more_articles = sorted([x for x in b.database["articles"].values()
                                if unread_with_keyword(x)],
                               key=b.relevance_of_article)
        HASHED.update({hash(x["link"]): x["link"] for x in more_articles})

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
