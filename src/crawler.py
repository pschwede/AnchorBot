#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import urllib
import re
import Image as PIL
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
re_clean = re.compile(
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
        '|youtu\.be/[-\w]+' +
        '|youtube\.com/watch?v=[-\w]+' +
        '|youtube\.com/v/[-\w]+' +
        '|youtube\.com/embed/[-\w]+' +
        ")", re.I)
re_splitter = re.compile("\W", re.UNICODE)
re_markdown_images = re.compile("!\[[^\]]*\]\([^\)]*\)")
css_textsel = CSSSelector("div,span,p")
css_imagesel = CSSSelector("img")
css_linksel = CSSSelector("a")
htmlunescape = HTMLParser.HTMLParser().unescape

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
        self.logger = logging.getLogger("root")

    def __textual_content(self, url=None, html=None, similarcontent=None):
        return self.clean(html)

    def crawlHTML(self, html, url, similarcontent=None, depth=0, baseurl=None):
        self.logger.debug("Crawling url=%s" % url)
        content = ""
        images = media = []
        try:
            if html:
                html = self.check_codec(html)
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
                except Exception, e:
                    self.logger.error("Error crawling HTML: %s", repr(e))
        except KeyboardInterrupt:
            pass
        return (set(images), content, media[0] if media else None,)

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
            htmltext = re_clean.sub("", htmltext)
        return htmltext

    def get_link(self, entry):
        link = ""
        try:
            link = entry.link
        except AttributeError:
            try:
                link = entry["links"][0]["href"]
            except KeyError:
                self.logger.warn( "%s has no link!" % entry["title"])
        return link.encode('utf-8')

    def search_in_html_of_entry(self, cached_url, url, entry):
        """Searches for content at three different places in entry."""
        images, content, media = set([]), "", []

        try:
            html = entry["content"][0]["value"]
            return self.crawlHTML(html=html, url=cached_url, baseurl=url)
        except KeyError:
            pass

        try:
            html = entry["summary_detail"]["value"]
            return self.crawlHTML(html=html, url=cached_url, baseurl=url)
        except KeyError:
            pass

        try:
            html = entry["summary"]["value"]
            return self.crawlHTML(
                    html=html, url=cached_url, baseurl=url)
        except KeyError:
            content = entry["title"]
        return images, content, media

    def check_codec(self, text):
        try:
            return text.encode("utf-8")
        except Exception, e:
            self.logger.debug("Exception: %s" % e)
        return text

    def get_images_from_entry(self, entry):
        """Searches for images in links and enclosures of entry"""
        images = set([])
        for key in ("links", "enclosures"):
            try:
                i = filter(lambda x: x["type"].startswith("image"),
                        entry[key])
                images |= set([item.href.encode("utf-8") for item in i])
            except KeyError:
                pass
        return images

    def get_content_from_url(self, cached_url, url):
        try:
            f = open(cached_url, 'r')
            result = self.crawlHTML(
                    html=f.read(), url=url, baseurl=url)
            f.close()
        except:
            result = ""
        finally:
            return result

    def enrich(self, entry, source, recursion=1):
        """Filters out images, adds images from html, cleans up content."""
        image, images = None, set([])
        content, media = "", list()
        url = self.get_link(entry)
        self.logger.info("Enriching %s" % url)
        # get more text and images
        cached_url = self.cache[url]
        if cached_url:
            # search in html content of the entry
            images, content, media = self.search_in_html_of_entry(cached_url,
                    url, entry)

            # get images from entry itself
            images |= self.get_images_from_entry(entry)

            # get even more images from the article, the entry links to
            more_images, more_content, more_media = self.get_content_from_url(
                    cached_url, url)            
            images |= more_images
            if more_content is not None and\
                    len(more_content) > len(content) and\
                    len(more_content) < 5000:
                content = more_content
            media = more_media

        # filter out some images
        images = self.filter_images(images, minimum=(40, 40,))

        # give the images to the entry finally
        image = self.biggest_image(images)
        self.logger.debug("image set: %s" % image)

        try:
            date = mktime(entry.updated_parsed)
        except AttributeError:
            date = time()

        if media is not None:
            self.logger.debug("Found media: %s" % media)

        title = entry["title"]
        art = Article(date, title, content, url, source)
        keywords = get_keywords(title)
        return art, list(set(keywords)), image, media
