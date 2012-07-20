#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import sys
from config import DBPATH
from sqlalchemy import desc
from datamodel import get_session_from_new_engine, Article, Keyword
from html2text import html2text
import humanize
import datetime
import time


def latest_articles(keyword=None, top=0, number=5):
    s = get_session_from_new_engine(DBPATH)
    articles = s.query(Article)
    if keyword:
        articles = articles.join(Article.keywords).\
        filter(Keyword.word == keyword)
    articles = list(
            articles.order_by(desc(Article.date)).\
            group_by(Article.title).\
            offset(top * number).limit(number))
    s.close()
    return articles

def print_articles(articles):
    for i, article in zip(range(len(articles)), articles):
        print "### %i) %s\n\n%s\n%s - [Read more](%s)\n----\n" % (
            i+1,
            article.title,
            html2text(article.content,
                article.link),
            humanize.naturalday(
                datetime.datetime.now() - \
                        datetime.timedelta(
                            seconds=time.time() - article.date)),
            article.link
            )

if __name__ == "__main__":
    if len(sys.argv) > 1:
        word = unicode(sys.argv[-1]).lower()
        if "-n"  in sys.argv:
            number = int(sys.argv[sys.argv.index("-n")+1])
            articles = latest_articles(word, number=number)
        else:
            articles = latest_articles(word)
        length = len(articles)
        print "## %i latest Article%s about %s\n" % (
                length, 
                length > 1 and "s" or "",
                word)
    else:
        articles = latest_articles()
        length = len(articles)
        print "## %i latest Article%s\n" % (
                length, 
                length > 1 and "s" or "")
    print_articles(articles)
