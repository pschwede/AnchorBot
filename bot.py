#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import sys
import json
import atexit
import pprint
import justext
import logging
import requests
import feedparser
from PIL import Image
from time import time, sleep
#from Queue import Queue
from socket import timeout
from StringIO import StringIO
#from threading import Thread
from redis_collections import Dict, Set, Counter

from Queue import Empty
from multiprocessing import JoinableQueue, Process, cpu_count, Queue, Pool
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings()

re_youtube = re.compile('((?<=watch\?v=)[-\w]+\
        |(?<=youtube.com/embed/)[-\w]+)', re.I)

re_images = re.compile('(?<=")[^"]+jpg(?=")', re.I)
re_splitter = re.compile("[^\w@#]+", re.UNICODE)

HOME = os.path.join(os.path.expanduser("~"), ".config/anchorbot")
HERE = os.path.realpath(os.path.dirname(__file__))
CONFIGFILE = os.path.join(HOME, "config")
NUM_THREADS = max(1, cpu_count() - 1)

class Config(dict):
    def __init__(self, configfile):
        dict.__init__(self)

        self["redis_keys"] = {}
        self["abos"] = []
        self.configfile = configfile

        if not os.path.exists(HOME):
            os.mkdir(HOME)
        if os.path.exists(configfile):
            if os.path.getsize(configfile) > 0:
                with open(configfile, "r") as f:
                    content = json.load(f)
                self.update(content)
            else:
                logging.warn("Empty config found. Creating new one.")
                os.remove(configfile)

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
    #print "loading %s" % href

    tries = 5
    while tries:
        try:
            response = requests.get(href, timeout=1.0, verify=False)
            if response:
                #print "loaded %s" % href
                return response.content
        except (timeout, requests.Timeout, requests.ConnectionError):
            pass
        finally:
            tries -= 1

    return ""


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


def find_keywords(title):
    return set([x.lower() for x in re_splitter.split(title) if x])


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

    page = get_html(entry.link)
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

    keywords = find_keywords(entry.title)
    article = {"link": entry.link,
               "title": entry.title,
               "release": time(),
               "content": content,
               "media": media,
               "image": picture,
               "keywords": keywords,
               "read": False,
               }
    #print "got article %s" % article["link"]
    return article


def __feed_worker(pid, inqueue, outqueue):
    try:
        while True:
            feedurl = inqueue.get(timeout=1)
            logging.debug("%i Queueing %s", pid, feedurl)
            try:
                response = requests.get(feedurl, timeout=1.0, verify=False)
            except (requests.Timeout, requests.ConnectionError):
                logging.debug("%i Timeout %s", pid, feedurl)
                inqueue.task_done()
                continue
            except requests.exceptions.MissingSchema:
                feedurl = "http://%s" % feedurl
                try:
                    response = requests.get(feedurl, timeout=1.0, verify=False)
                except:
                    logging.debug("%i Cannot handle %s", pid, feedurl)
                    inqueue.task_done()
                    continue
            if response.status_code != 200:
                logging.warn("%i Non-200 status code %i: %s", pid, response.status_code, feedurl)
            feed = feedparser.parse(response.text)
            logging.debug("%i There are %i entries in %s", pid, len(feed.entries), feedurl)
            for entry in feed.entries:
                if entry.link not in db["articles"]:
                    logging.debug("%i put %s" , pid, entry.link)
                    outqueue.put(entry)
                else:
                    logging.debug("%i ign %s" , pid, entry.link)
            inqueue.task_done()
    except Empty:
        pass


def __art_worker(pid, queue):
    try:
        while True:
            entry = queue.get(timeout=1)
            logging.debug("%i Getting %s", pid, entry.link)
            article = get_article(entry)
            db["articles"][article["link"]] = article
            queue.task_done()
    except Empty:
        pass


def __progress(pid, queue):
    maximum = 1
    tick = 0
    tstart = time()
    while True:
        remaining = queue.qsize()
        maximum = max(remaining, maximum)
        percent = 1. - float(remaining) / maximum
        testimated = max(0.01, percent) * (time() - tstart) / (1.001 - percent) 
        size = int(40 * percent)
        bar = "=" * size + " " * (50 - size)
        throbber = "-\\|/"[tick % 4] if percent < 1 else "X"
        sys.stdout.write("%c %3i%% [ %s ] (%i of %i, %i sec)\r" % \
                (throbber, 100 * percent, bar, maximum - remaining, maximum, testimated/100))
        tick += 1
        if percent >= 1:
            print
            return
        sleep(0.10)


def run_processes(target, inqueue, outqueue=None):
    threads = max(1, (NUM_THREADS - 1))
    for n in range(threads):
        if outqueue:
            p = Process(target=target, args=(n, inqueue, outqueue))
        else:
            p = Process(target=target, args=(n, inqueue))
        p.daemon = True
        p.start()
    pp = Process(target=__progress, args=(-1, inqueue))
    pp.daemon = True
    pp.start()
    inqueue.close()
    inqueue.join()


def curate(db):
    art_queue = JoinableQueue()
    feed_queue = JoinableQueue()

    for feedurl in abo_urls(db["subscriptions"]):
        feed_queue.put(feedurl)
    
    print "Downloading %i feeds.." % feed_queue.qsize()
    run_processes(__feed_worker, feed_queue, art_queue)

    print "Downloading %i articles.." % art_queue.qsize()
    run_processes(__art_worker, art_queue)

    print "Done."


def display(articles):
    pprint.pprint(articles.values())


if __name__ == "__main__":
    logging.basicConfig()
    #logging.basicConfig(level=logging.DEBUG)
    logging.debug(HOME, HERE, CONFIGFILE, NUM_THREADS)

    config = Config(CONFIGFILE)
    db = initialize_database(config)
    atexit.register(config.save, db)

    config["abos"] += ["http://usesthis.com/feed/",
                       "http://feeds.theguardian.com/theguardian/uk/rss",
                       "http://github.com/pschwede/AnchorBot/commits/master.atom",
                       "http://www.youtube.com/user/TheSustainableMan",
                       ]
    for abo in config["abos"]:
        subscribe_feed(db["subscriptions"], abo)
    curate(db)
    #display(db["articles"])
