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
from subprocess import check_output

from hyphenator import Hyphenator
#from boilerpipe.extract import Extractor


"""
Generic crawler.
Follows redirections and delivers some useful functions for remote images.
"""
re_cln = re.compile('(<img[^>]+>|[\n\r]|<script[^>]*>\s*</script>|<iframe.*</iframe>|</*html>|</*head>|</*div[^>]*>| [ ]+)', re.I)
re_textual = re.compile("((<([abip]|li|ul|img|span|strong)[^>]*>.*)+(</([abip]|li|ul|span|strong)>.*)+)+", re.U + re.I)

class Crawler(object):
    hyph_EN = "/usr/share/hyphen/hyph_en_US.dic"
    hyph_DE = "/usr/share/hyphen/hyph_de_DE.dic"
    hyph_FR = "/usr/share/hyphen/hyph_fr_FR.dic"
    htmlparser = HTMLParser()

    def __init__(self, cacher, analyzer, proxies=None, verbose=False):
        self.opener = urllib.FancyURLopener(proxies)
        self.cache = cacher # for not retrieving things twice!
        self.verbose = verbose
        self.analyzer = analyzer

        self.hyphenator = None
        try:
            self.hyphenator = Hyphenator(self.hyph_DE)
        except IOError:
            self.verbose and log("Not using hyphenator since %s can not be loaded." % self.hyph_DE)

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

            # regex method (not working; wrong re_textual!)
            #content = sorted([x[0] for x in re_textual.findall(html)], key=lambda x: len(x.split(" ")), reverse=True)[0]


            # naive method
            content = similarcontent or html
            if similarcontent:
                textsel = CSSSelector("div,span,p")
                for elem in textsel(tree):
                    if elem.text and similarcontent[:-len(similarcontent)/2] in elem.text:
                        content = elem.text
        else:
            if url:
                #try:
                # boilerpipe port
                f = open(url, 'r')
                text = xmltostring(xmlfromstring(f.read(), self.htmlparser))
                #content = Extractor('DefaultExtractor', url="file://"+url).getText()
                f.close()
                #except Exception, e:
                #self.verbose and log("Fail @%s, %s"%(url, e))

        return content

    def crawlHTML(self, html, url, similarcontent=None, depth=0, baseurl=None):
        self.verbose and log("Crawling url=%s"%url)
        tree = soupparser.fromstring(html) 

        imagesel = CSSSelector("img")
        images = [urljoin(baseurl, img.get("src") or img.attrib.values()[0]) for img in imagesel(tree)]

        linksel = CSSSelector("a")
        for elem in linksel(tree):
            link = urljoin(baseurl, elem.get("href"))
            if link and link[-4:] in (".png", ".jpg", ".gif", "jpeg"):
                images.append(link)

        content = self.__textual_content(html=xmltostring(tree), similarcontent=similarcontent)
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
        biggest = u""
        imagelist = list(set(imagelist))
        x, y = 0, 0
        errors = []
        for imgurl in imagelist:
            try:
                im = PIL.open(self.cache[imgurl])
                if x * y < im.size[0] * im.size[1]:
                    x, y = im.size
                    biggest = imgurl
            except IOError:
                errors.append(imgurl)
        if errors and self.verbose:
            self.verbose and log("PIL: " + str(errors))
        return biggest

    def closest_image(self, imagelist, x, y):
        closest = None
        dx, dy = 10 ** 10, 10 ** 10
        errors = []
        for imgurl in imagelist:
            try:
                im = PIL.open(self.cache[imgurl])
                if dx / dy > abs(im.size[0] - x) / abs(im.size[1] - y):
                    dx, dy = abs(im.size[0] - x), abs(im.size[1] - y)
                    closest = imgurl
            except IOError:
                errors.append(self.cache[imgurl])
        if errors and self.verbose:
            self.verbose and log("PIL: " + str(errors))
        return closest

    def filter_images(self, images, minimum=None, maximum=None):
        if not minimum and not maximum:
            return images
        else:
            minimum = minimum or (0, 0,)
            maximum = maximum or (9999, 9999,)

        result = []
        for imgurl in images:
            try:
                im = PIL.open(self.cache[imgurl])
                if im.size[0] >= minimum[0] and im.size[1] >= minimum[1] and\
                     im.size[0] <= maximum[0] and im.size[1] <= maximum[1]:
                        result.append(imgurl)
            except IOError:
                self.verbose and log("Can't open that file: %s" % self.cache[imgurl])
        return result

    def clean(self, htmltext):
        """Removes tags and adds optional hyphens (&shy;) to each word or sentence."""
        if self.hyphenator:
            tree = soupparser.fromstring(unicode(htmltext, "utf-8"))
            self.recursive_hyph(tree)
            htmltext = xmltostring(tree, encoding="utf8")
        tmp = u""
        while hash(tmp) != hash(htmltext):
            tmp = htmltext
            htmltext = re_cln.sub("", htmltext)
        return htmltext

    def recursive_hyph(self, tree, hyphen=u"\u00ad"):
        try:
            if tree.text:
                tree.text = self.hyphenator.inserted(tree.text, hyphen)
            if tree.tail:
                tree.tail = self.hyphenator.inserted(tree.tail, hyphen)
        except UnicodeDecodeError, e:
            if self.verbose:
                print "W: %s" % e.message

        for elem in tree:
            self.recursive_hyph(elem, hyphen)

    def get_link(self, entry):
        link = ""
        try:
            link = entry.link
        except AttributeError:
            try:
                link = entry["links"][0]["href"]
            except KeyError:
                print "Warning! %s has no link!" % entry["title"]
        return link

    def enrich(self, entry, source, recursion=1):
        """Filters out images, adds images from html, cleans up content."""
        image = None
        images = set()
        url = self.get_link(entry)
        # get more text and images
        try:
            html = entry["content"][0].value
            images, content = self.crawlHTML(html, self.cache[url])
        except KeyError:
            try:
                html = entry["summary_detail"].value
                images, content = self.crawlHTML(html, self.cache[url])
            except KeyError:
                try:
                    html = entry["summary"].value
                    images, content = self.crawlHTML(html, self.cache[url])
                except KeyError:
                    content = entry["title"]

        # get images from entry itself
        for key in ("links", "enclosures"):
            try:
                i = filter(lambda x: x.type.startswith("image"), entry[key])
            except KeyError:
                pass
            images |= set([item.href.decode("utf-8") for item in i])

        # get even more images from links in entry
        try:
            for link in entry["links"]:
                if link["href"]:
                    # check for encoding
                    f = open(self.cache[link["href"]])
                    html = f.read()
                    if html:
                        codec = chardet.detect(html)["encoding"]
                        if codec:
                            htmlutf8 = unicode(html, codec)
                            if htmlutf8:
                                html = htmlutf8
                        try:
                            imgs, cont = self.crawlHTML(#@UnusedVariable
                                html,
                                self.cache[link],
                                baseurl=link["href"],
                              )
                            images |= imgs
                            #content += cont # Ignore more content for now.
                        except Exception, e:
                            if type(e).__name__ == "ValueError":
                                self.verbose and log("Wrong char? %s" % e)
                            else:
                                self.verbose and log("%s" % e)

        except KeyError:
            self.verbose and log("There were no links: %s" % entry)

        # filter out some images
        # give the images to the entry finally
        images = self.filter_images(images, minimum=(40, 40,))
        if not image or image.endswith("gif"):
            image = self.biggest_image(images)
        #TODO resize image to a prefered size here!


        try:
            date = mktime(entry.updated_parsed)
        except AttributeError:
            date = time()

        title = entry["title"]
        a = self.analyzer
        a.add({a.eid: link, a.key: title})
        keywords = [Keyword(kw) for kw in a.get_keywords_of_article({a.eid: link, a.key: title})]
        art = Article(date, title, content, url, source, Image(image))
        return art, keywords
