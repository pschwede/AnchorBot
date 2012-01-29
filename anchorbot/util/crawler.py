#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import urllib, re, Image as PIL
import chardet
from urlparse import urljoin
from lxml.cssselect import CSSSelector
from lxml.html import soupparser
from lxml.etree import tostring as xmltostring, fromstring as xmlfromstring, HTMLParser
from logger import log
from time import mktime, time
from datamodel import Article, Image, Keyword

#from boilerpipe.extract import Extractor


"""
Generic crawler.
Follows redirections and delivers some useful functions for remote images.
"""
re_cln = re.compile('(<img[^>]+>|[\n\r]|<script[^>]*>\s*</script>|<iframe.*</iframe>|</*html>|</*head>|</*div[^>]*>| [ ]+)', re.I)
re_splitter = re.compile("\W", re.UNICODE)
css_textsel = CSSSelector("div,span,p")
css_imagesel = CSSSelector("img")
css_linksel = CSSSelector("a")

class Crawler(object):
    htmlparser = HTMLParser()

    def __init__(self, cacher, proxies=None, verbose=False):
        self.opener = urllib.FancyURLopener(proxies)
        self.cache = cacher # for not retrieving things twice!
        self.verbose = verbose

    def __textual_content(self, url=None, html=None, similarcontent=None):
        content = ""
        if html:
            # clean up codec
            try:
                codec = chardet.detect(html)["encoding"]
                if codec:
                    html = html.encode(codec, "xmlcharrefreplace")
            except UnicodeDecodeError, e:
                print "Unencodable character found.", e

            # regex method (not working; broken re_textual!)
            #content = sorted([x[0] for x in re_textual.findall(html)], key=lambda x: len(x.split(" ")), reverse=True)[0]


            # naive method
            content = similarcontent or html
            if similarcontent:
                length = len(similarcontent)/2
                for elem in css_textsel(tree):
                    if elem.text and similarcontent[0:length] in elem.text:
                        content += elem.text
        else:
            if url:
                try:
                # boilerpipe port
                    content += Extractor('ArticleExtractor', url="file://"+url).getText()
                    f.close()
                except Exception, e:
                    self.verbose and log("Fail @%s, %s"%(url, e))

        return content

    def crawlHTML(self, html, url, similarcontent=None, depth=0, baseurl=None):
        self.verbose and log("Crawling url=%s"%url)
        content = ""
        images = []
        if html:
            try:
                tree = soupparser.fromstring(html) 
                content = self.__textual_content(html=xmltostring(tree), similarcontent=similarcontent)

                images = [urljoin(baseurl, img.get("src") or img.attrib.values()[0]) \
                        for img in css_imagesel(tree)]
                images + [urljoin(baseurl, elem.get("href")) \
                        for elem in css_linksel(tree) \
                            if elem is not None and elem.get("href") is not None \
                                and elem.get("href")[-4:] not in \
                                    (".png", ".jpg", ".gif", "jpeg")]
            except ValueError, e:
                log(e.message)
        return (set(images), self.clean(content),)

    def unescape(self, text):
        text = text.replace("\/", "/")
        text = text.replace("&quot;", "\"")
        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")
        return text

    def compare_image(self, im1, im2):
        im = PIL.open(self.cache[im1])
        x1, y1 = im.size
        im = PIL.open(self.cache[im2])
        x2, y2 = im.size
        if x1 * y1 < x2 * y2:
            return -1
        elif x1 * y1 == x2 * y2:
            return 0
        return 1

    def biggest_image(self, imagelist):
        biggest = ""
        imagelist = list(set(imagelist))
        x, y = 0, 0
        for imgurl in imagelist:
            try:
                im = PIL.open(self.cache[imgurl])
                if x*y < im.size[0]*im.size[1]:
                    x, y = im.size
                    biggest = imgurl
            except IOError:
                pass
        return biggest

    def closest_image(self, imagelist, x, y):
        closest = None
        imagelist = list(set(imagelist))
        dx, dy = 10 ** 10, 10 ** 10
        for imgurl in imagelist:
            try:
                im = PIL.open(self.cache[imgurl])
                if dx / dy > abs(im.size[0] - x) / abs(im.size[1] - y):
                    dx, dy = abs(im.size[0] - x), abs(im.size[1] - y)
                    closest = imgurl
            except IOError:
                pass
        return closest

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
            except Exception, e:
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
                print "Warning! %s has no link!" % entry["title"]
        return link.encode('utf-8')

    def enrich(self, entry, source, recursion=1):
        """Filters out images, adds images from html, cleans up content."""
        image = None
        images = set()
        content = ""
        url = self.get_link(entry)
        print "enriching", url
        # get more text and images
        cached_url = self.cache[url]
        try:
            html = entry["content"][0]["value"]
            images, content = self.crawlHTML(html, cached_url, baseurl=url)
        except KeyError:
            try:
                html = entry["summary_detail"]["value"]
                images, content = self.crawlHTML(html, cached_url, baseurl=url)
            except KeyError:
                try:
                    html = entry["summary"]["value"]
                    images, content = self.crawlHTML(html, cached_url, baseurl=url)
                except KeyError:
                    content = entry["title"]

        # get images from entry itself
        for key in ("links", "enclosures"):
            try:
                i = filter(lambda x: x["type"].startswith("image"), entry[key])
                images |= set([item.href.decode("utf-8") for item in i])
            except KeyError:
                pass

        # get even more images from links in entry
        f = open(self.cache[url], 'r')
        html = f.read()
        codec = chardet.detect(html)["encoding"]
        if codec:
            html = html.decode(codec)
        new_images, more_content = self.crawlHTML(html, url, baseurl=url)
        images |= new_images
        done = False
        #content = len(more_content)>len(content) and more_content or content

        # filter out some images
        # give the images to the entry finally
        images = self.filter_images(images, minimum=(40, 40,))
        if not image:
            image = self.biggest_image(images)
        #TODO resize image to a prefered size here!

        try:
            date = mktime(entry.updated_parsed)
        except AttributeError:
            date = time()

        title = entry["title"]
        keywords = [unicode(kw.lower()) for kw in re_splitter.split(title) if len(kw)>2]
        art = Article(date, title, content, url, source,)
        return art, list(set(keywords)), image
