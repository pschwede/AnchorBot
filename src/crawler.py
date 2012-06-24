#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import urllib
import re
import Image as PIL
import chardet
from urlparse import urljoin
from lxml.cssselect import CSSSelector
from lxml.html import soupparser
from lxml.etree import (
        tostring as xmltostring,
        HTMLParser)
from logger import log
from time import mktime, time
from datamodel import Article
from html2text import html2text

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
        "|youtu\.be/[^\"]+" +
        "|youtube\.com/watch?v=[^\"]+" +
        "|youtube\.com/watch?[^&]+&[^\"]+" +
        "|http://www.youtube\.com/v/[^\"]+" +
        "|http://www.youtube\.com/embed/[^\"]+" +
        ")", re.I)
re_splitter = re.compile("\W", re.UNICODE)
css_textsel = CSSSelector("div,span,p")
css_imagesel = CSSSelector("img")
css_linksel = CSSSelector("a")


class Crawler(object):
    htmlparser = HTMLParser()

    def __init__(self, cacher, proxies=None, verbose=False):
        self.opener = urllib.FancyURLopener(proxies)
        self.cache = cacher  # for not retrieving things twice!
        self.verbose = verbose

    def __textual_content(self, url=None, html=None, similarcontent=None):
        """ If url is set and html is not, it uses BoilerPipe
        """
        content = html2text(html)
        return content

    def crawlHTML(self, html, url, similarcontent=None, depth=0, baseurl=None):
        self.verbose and log("Crawling url=%s" % url)
        content = ""
        images = media = []
        try:
            if html:
                tree = soupparser.fromstring(html)
                content = self.__textual_content(
                        html=xmltostring(tree),
                        similarcontent=similarcontent)
                images = list()
                for img in css_imagesel(tree):
                    images.append(urljoin(baseurl,
                        img.get("src") or img.attrib.values()[0]))
                for elem in css_linksel(tree):
                    if elem and elem.get("href"):
                        href = elem.get("href")
                        if href[4:] == "http":
                            endings = (".png", ".jpg", ".gif", "jpeg")
                            if href[:4] in endings:
                                images.append(urljoin(baseurl, elem.get("href")))
                media += re_media.findall(html) or ""
        except KeyboardInterrupt:
            pass
        return (set(images), self.clean(content), media[-1] if media else None)

    def unescape(self, text):
        text = text.replace("\/", "/")
        text = text.replace("&quot;", "\"")
        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")
        return text

    def biggest_image(self, imagelist):
        biggest = ""
        imagelist = list(set(imagelist))
        x, y = 0, 0
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
                self.verbose and log( "Warning! %s has no link!" % entry["title"])
        return link.encode('utf-8')

    def enrich(self, entry, source, recursion=1):
        """Filters out images, adds images from html, cleans up content."""
        image = None
        images = set()
        content = ""
        media = list()
        url = self.get_link(entry)
        self.verbose and log( "Enriching %s" % url)
        # get more text and images
        cached_url = self.cache[url]
        if cached_url:
            try:
                html = entry["content"][0]["value"]
                images, content, media = self.crawlHTML(
                        html, cached_url, baseurl=url)
            except KeyError:
                try:
                    html = entry["summary_detail"]["value"]
                    images, content, media = self.crawlHTML(
                            html, cached_url, baseurl=url)
                except KeyError:
                    try:
                        html = entry["summary"]["value"]
                        images, content, media = self.crawlHTML(
                                html, cached_url, baseurl=url)
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
                    html, url, baseurl=url)
            images |= new_images
            """
            if len(more_content) > len(content):
                content = more_content
            """

        # filter out some images
        # give the images to the entry finally
        self.cache.get_all(images)
        images = self.filter_images(images, minimum=(40, 40,))
        #print images
        if not image:
            image = self.biggest_image(images)
        #TODO resize image to a prefered size here!

        try:
            date = mktime(entry.updated_parsed)
        except AttributeError:
            date = time()

        if media:
            self.verbose and log(u"Found media: %s" % unicode(media))

        title = entry["title"]
        keywords = list()
        for kw in re_splitter.split(title):
            keywords.append(unicode(kw.lower()))
        art = Article(date, title, content, url, source)
        return art, list(set(keywords)), image, media
