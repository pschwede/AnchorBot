#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import urllib
import re
import Image as PIL
import chardet
import logging
from urlparse import urljoin
from lxml.cssselect import CSSSelector
from lxml.html import soupparser
from time import mktime, time
from datamodel import Article
import HTMLParser

#from boilerpipe.extract import Extractor


"""
Generic crawler.
Follows redirections and delivers some useful functions for remote images.
"""
re_cln = re.compile(
        '(<img[^>]+>' +
        '|[\n\r]|<script[^>]*>\s*</script>' +
        '|<iframe.*</iframe>' +
        '|</*html>' +
        '|</*head>' +
        '|</*div[^>]*>' +
        '| [ ]+' +
        'style="[^"]*"' +
        ')', re.I)
re_media = re.compile(
        "(http://\S.mp3" +
        "|vimeo\.com/\d+" +
        '|youtu\.be/[-\w]+[^"]' +
        '|youtube\.com/watch?v=[-\w]+[^"]' +
        '|youtube\.com/watch?[^&]+&[-\w]+[^"]' +
        '|youtube\.com/v/[-\w]+[^"]' +
        '|youtube\.com/embed/[-\w]+[^"]' +
        ")", re.I)
re_splitter = re.compile("\W", re.UNICODE)
re_mdimages = re.compile("!\[[^\]]*\]\([^\)]*\)")
css_textsel = CSSSelector("div,span,p")
css_imagesel = CSSSelector("img")
css_linksel = CSSSelector("a")
htmlunescape = HTMLParser.HTMLParser().unescape

logger = logging.getLogger("root")

def get_keywords(title, forjinja2=False):
    keywords = list()
    if not forjinja2:
        for kw in re_splitter.split(htmlunescape(title).lower()):
            if len(kw)>1:
                keywords.append(unicode(kw))
    else:
        for kw in title.split(" "):
            if len(kw)>1:
                keywords.append(unicode(kw))
    return keywords


class Crawler(object):
    def __init__(self, cacher, proxies=None):
        self.opener = urllib.FancyURLopener(proxies)
        self.cache = cacher  # for not retrieving things twice!

    def __textual_content(self, url=None, html=None, similarcontent=None):
        return self.clean(html)

    def crawlHTML(self, html, url, similarcontent=None, depth=0, baseurl=None):
        logger.debug("Crawling url=%s" % url)
        content = ""
        images = media = []
        try:
            if html:
                content = self.__textual_content(
                        html=html,
                        similarcontent=similarcontent)
                media += re_media.findall(html) or ""
                try:
                    tree = soupparser.fromstring(html)
                    for img in css_imagesel(tree):
                        images.append(urljoin(baseurl,
                            img.get("src") or img.attrib.values()[0]))
                    for elem in css_linksel(tree):
                        if elem is not None and elem.get("href"):
                            href = elem.get("href")
                            if href[4:] == "http":
                                endings = (".png", ".jpg", ".gif", "jpeg")
                                if href[:4] in endings:
                                    images.append(urljoin(baseurl, elem.get("href")))
                except TypeError:
                    pass
        except KeyboardInterrupt:
            pass
        return (set(images), content, media[0] if media else None)

    def biggest_image(self, imagelist):
        biggest = ""
        imagelist = list(set(imagelist))
        x, y = 0, 0
        self.cache.get_all(imagelist)
        for imgurl in imagelist:
            try:
                im = PIL.open(self.cache[imgurl])
                if x * y < im.size[0] * im.size[1]:
                    x, y = im.size
                    biggest = imgurl
            except IOError:
                pass
        return biggest

    def filter_images(self, images, minimum=None, maximum=None):
        if not minimum and not maximum:
            return images
        else:
            minimum = minimum or (0, 0,)
            maximum = maximum or (9999, 9999,)

        images = list(set(images))
        result = []
        self.cache.get_all(images)
        for imgurl in images:
            try:
                im = PIL.open(self.cache[imgurl])
                if im.size[0] >= minimum[0] and im.size[1] >= minimum[1] and\
                     im.size[0] <= maximum[0] and im.size[1] <= maximum[1]:
                        result.append(imgurl)
            except Exception:
                pass
        return result

    def clean(self, htmltext):
        """Removes tags to each word or sentence."""
        tmp = u""
        while hash(tmp) != hash(htmltext):
            tmp = htmltext
            htmltext = re_cln.sub("", htmltext)
        return htmltext

    def get_link(self, entry):
        link = ""
        try:
            link = entry.link
        except AttributeError:
            try:
                link = entry["links"][0]["href"]
            except KeyError:
                logger.warn( "%s has no link!" % entry["title"])
        return link.encode('utf-8')

    def enrich(self, entry, source, recursion=1):
        """Filters out images, adds images from html, cleans up content."""
        image = None
        images = set()
        content = ""
        media = list()
        url = self.get_link(entry)
        logger.debug( "Enriching %s" % url)
        # get more text and images
        cached_url = self.cache[url]
        if cached_url:
            try:
                html = entry["content"][0]["value"]
                images, content, media = self.crawlHTML(
                        html=html, url=cached_url, baseurl=url)
            except KeyError:
                try:
                    html = entry["summary_detail"]["value"]
                    images, content, media = self.crawlHTML(
                            html=html, url=cached_url, baseurl=url)
                except KeyError:
                    try:
                        html = entry["summary"]["value"]
                        images, content, media = self.crawlHTML(
                                html=html, url=cached_url, baseurl=url)
                    except KeyError:
                        content = entry["title"]

            # get images from entry itself
            for key in ("links", "enclosures"):
                try:
                    i = filter(lambda x: x["type"].startswith("image"),
                            entry[key])
                    images |= set([item.href.decode("utf-8") for item in i])
                except KeyError:
                    pass

            # get even more images from links in entry
            f = open(cached_url, 'r')
            html = f.read()
            codec = chardet.detect(html)["encoding"]
            if codec:
                try:
                    html = html.decode(codec)
                except:
                    pass
            new_images, more_content, media = self.crawlHTML(
                    html=html, url=url, baseurl=url)
            images |= new_images
            if more_content is not None and\
                    len(more_content) > len(content) and\
                    len(more_content) < 5000:
                content = more_content

        # filter out some images
        # give the images to the entry finally
        images = self.filter_images(images, minimum=(40, 40,))
        #print images
        if image is None:
            image = self.biggest_image(images)
            self.logger.debug("image set: %s" % image)
        #TODO resize image to a prefered size here!

        try:
            date = mktime(entry.updated_parsed)
        except AttributeError:
            date = time()

        if media is not None:
            logger.debug(u"Found media: %s" % unicode(media))

        title = entry["title"]
        art = Article(date, title, content, url, source)
        keywords = get_keywords(title)
        return art, list(set(keywords)), image, media
