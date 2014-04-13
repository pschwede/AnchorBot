#!/usr/bin/env python

import os
import re
import json
import atexit
import pprint
import justext
import requests
import feedparser
from PIL import Image
from time import time
from Queue import Queue
from socket import timeout
from StringIO import StringIO
from threading import Thread
from redis_collections import Dict, Set, Counter

re_youtube = re.compile('((?<=watch\?v=)[-\w]+\
        |(?<=youtube.com/embed/)[-\w]+)', re.I)

re_images = re.compile('(?<=")[^"]+jpg(?=")', re.I)
re_splitter = re.compile("\s", re.UNICODE)

HOME = os.path.join(os.path.expanduser("~"), ".config/anchorbot")
HERE = os.path.realpath(os.path.dirname(__file__))
CONFIGFILE = os.path.join(HOME, "config")


class Config(dict):
    def __init__(self, configfile):
        dict.__init__(self)

        self["redis_keys"] = {}
        self["abos"] = []
        self.configfile = configfile

        if not os.path.exists(HOME):
            os.mkdir(HOME)
        if os.path.exists(configfile):
            with open(configfile, "r") as f:
                self.update(json.load(f))

    def save(self, db):
        for name, piece in db.items():
            self["redis_keys"][name] = piece.key
        with open(self.configfile, "w") as f:
            self["abos"] = list(set(self["abos"]))
            json.dump(dict(self), f, indent=4)


def initialize_database(config):
    types = {"subscriptions": Set, "articles": Dict, "keyword_clicks": Counter}
    db = {key: val() for key, val in types.items()}
    for piece, key in config["redis_keys"].items():
        db[piece] = types[piece](key=key)
    return db


def subscribe_feed(subscriptions, feedurl):
    subscriptions.add({"feedurl": feedurl, "cycle": 1})


def unsubscribe_feed(subscriptions, feedurl):
    keyfunc = lambda x: x["feedurl"] == feedurl
    subscriptions -= filter(subscriptions, key=keyfunc)


def abo_urls(subscriptions):
    return [x["feedurl"] for x in subscriptions]


def get_html(href):
    if href[:-4] in [".pdf"]:
        return ""
    print "loading %s" % href

    tries = 5
    while tries:
        try:
            try:
                response = requests.get(href, timeout=1.0, verify=False)
            except requests.ConnectionError:
                return ""
            not_loaded = 0
        except timeout:
            pass
        finally:
            tries -= 1

    return response.content


def guess_language(html):
    hits = dict()
    htmlset = set(str(html).split(" "))
    for lang in justext.get_stoplists():
        hits[lang] = len(set(justext.get_stoplist(lang)).intersection(htmlset))
    return max(hits, key=hits.get)


def remove_boilerplate(html, language="English"):
    try:
        paragraphs = justext.justext(html, justext.get_stoplist(language))
    except:
        return html  # TODO alternative to justext
    tag = lambda p: ("%s\n----\n" if p.is_heading else "%s\n\n") % p.text
    content = "".join([tag(p) for p in paragraphs if not p.is_boilerplate])
    return content


def find_keywords(title, language="English"):
    stoplist = justext.get_stoplist(language)
    return set([x.lower() for x in re_splitter.split(title)
                if x.lower() not in stoplist])


def find_media(html):
    findings = re_youtube.findall(html)
    template = """
        <iframe width="560" height="315"
        src="//www.youtube.com/embed/%s" frameborder="0"
        allowfullscreen></iframe>
    """
    return template % findings[0] if findings else ""


def find_picture(html):
    biggest = ""
    x, y = 0, 0
    imagelist = re_images.findall(html)
    for imgurl in imagelist:
        try:
            try:
                binary = StringIO(requests.get(imgurl,
                                               timeout=1.0,
                                               verify=False).content)
                image = Image.open(binary)
                if x * y < image.size[0] * image.size[1]:
                    x, y = image.size
                    biggest = imgurl
            except IOError:
                continue
        except requests.packages.urllib3.exceptions.LocationParseError:
            pass
    return biggest


def get_article(entry):
    page = ""
    content = ""
    picture = ""
    media = ""

    try:
        page = get_html(entry.link)
    except requests.exceptions.Timeout:
        return
    language = guess_language(page)
    try:
        content = remove_boilerplate(page, language=language)
    except justext.core.JustextError:
        pass
    try:
        picture = find_picture(page)
    except requests.exceptions.Timeout:
        pass
    media = find_media(page)

    keywords = find_keywords(entry.title, language=language)
    article = {"link": entry.link,
               "title": entry.title,
               "release": time(),
               "content": content,
               "media": media,
               "image": picture,
               "keywords": keywords,
               "read": False,
               }
    return article


def curate(db):
    queue = Queue()

    def worker():
        while True:
            entry = queue.get()
            get_article(entry)
            queue.task_done()

    for feedurl in abo_urls(db["subscriptions"]):
        feed = feedparser.parse(feedurl)
        print "Queueing %s" % feedurl
        for entry in feed.entries:
            if entry.link not in db["articles"]:
                queue.put(entry)

    for i in range(15):
        t = Thread(target=worker)
        t.daemon = True
        t.start()

    queue.join()


def display(articles):
    pprint.pprint(articles.values())


if __name__ == "__main__":
    config = Config(CONFIGFILE)
    db = initialize_database(config)
    atexit.register(config.save, db)

    config["abos"] += ["http://usesthis.com/feed/",
                       "http://feeds.theguardian.com/theguardian/uk/rss",
                       "https://github.com/pschwede/AnchorBot/commits/master.a\
                               tom",
                       "https://www.youtube.com/user/TheSustainableMan",
                       ]
    for abo in config["abos"]:
        subscribe_feed(db["subscriptions"], abo)
    curate(db)
    #display(db["articles"])
