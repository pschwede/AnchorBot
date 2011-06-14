#!/usr/bin/env python

import urllib, re, mimetypes, os.path, Image
import chardet
from urlparse import urljoin
from lxml.cssselect import CSSSelector
from lxml.html import make_links_absolute, soupparser
from lxml.etree import tostring as xmltostring
from storage import PersistentCacher
from logger import log

"""
Follows redirections and delivers some useful functions for remote images.
"""

class Crawler(object):
    re_cln = re.compile('((<img[^>]+>)|(<div>\s*</div>)|[\n\r]|(<script.*</script>)|(<iframe.*</iframe>)|<html>|</html>)', re.I)

    def __init__(self, cacher, proxies=None, verbose=False):
        self.opener = urllib.FancyURLopener(proxies)
        self.cache = cacher # for not retrieving things twice!
        self.verbose = verbose

    def crawlHTML(self, tree, similarcontent=None, depth=0, baseurl=None):
        imagesel = CSSSelector("img")
        textsel = CSSSelector("div,span,p")
        content = similarcontent or xmltostring(tree)
        if similarcontent:
            for elem in textsel(tree):
                if elem.text and similarcontent[:-3] in elem.text:
                    content = elem.text
                    break;
        keepimage = None
        images = [urljoin(baseurl,img.get("src") or img.attrib.values()[0]) for img in imagesel(tree)]
        if images:
            keepimage = images[0]
        linksel = CSSSelector("a")
        for elem in linksel(tree):
            link = elem.get("href")
            if link and link[-4:] in (".png",".jpg",".gif","jpeg"):
                images.append(urljoin(baseurl, link))
        return {"image": keepimage, "images": images, "content": self.clean(content)}

    def unescape(self, text):
        text = text.replace("\/","/")
        text = text.replace("&quot;","\"")
        text = text.replace("&lt;","<")
        text = text.replace("&gt;",">")
        return text

    def compare_image(self, im1, im2):
        im = Image.open(self.cache[im1])
        x1, y1 = im.size
        im = Image(open(self.cache[im2]))
        x2, y2 = im.size
        if x1*y1 < x2*y2:
            return -1
        elif x1*y1 == x2*y2:
            return 0
        return 1

    def biggest_image(self, imagelist):
        biggest = None
        imagelist = list(set(imagelist))
        x, y = 0, 0
        errors =  []
        for imgurl in imagelist:
            try:
                im = Image.open(self.cache[imgurl])
                imgurl = self.cache[imgurl]
                if x * y < im.size[0] * im.size[1]:
                    x, y = im.size
                    biggest = imgurl
            except IOError:
                pass
        if errors and self.verbose:
            log("PIL: "+str(errors))
        return biggest

    def closest_image(self, imagelist, x, y):
        closest = None
        dx, dy = 10**10, 10**10
        errors = []
        for imgurl in imagelist:
            try:
                im = Image.open(self.cache[imgurl])
                if dx/dy > abs(im.size[0]-x) / abs(im.size[1]-y):
                    dx, dy = abs(im.size[0]-x), abs(im.size[1]-y)
                    closest = imgurl
            except IOError:
                errors.append(self.cache[imgurl])
        if errors and self.verbose:
            log("PIL: "+str(errors))
        return closest

    def filter_images(self, images, minimum=(0, 0,), maximum=(0, 0,)):
        if minimum == (0, 0,) and maximum == (0, 0,):
            return images

        result = []
        for imgurl in images:
            try:
                im = Image.open(self.cache[imgurl])
                if im.size[0] >= minimum[0] and im.size[1] >= minimum[1]:
                    if maximum == (0, 0,):
                        result.append(self.cache[imgurl])
                    elif im.size[0] <= maximum[0] and im.size[1] <= maximum[1]:
                        result.append(self.cache[imgurl])
            except IOError:
                pass
        return result

    def clean(self, htmltext):
        return self.re_cln.sub("", htmltext)

    def enrich(self, feed, recursion=1):
        # filters out images, adds images from html, cleans up content
        for entry in feed["entries"]:
            # get more text
            article = None
            try:
                content = entry["content"][0].value
                article = self.crawlHTML(soupparser.fromstring(content))
            except KeyError:
                try:
                    content = entry["summary_detail"].value
                    article = self.crawlHTML(soupparser.fromstring(content))
                except KeyError:
                    pass

            # get more images
            # from entry itself
            entry["image"] = None
            images = set()
            for key in ("links", "enclosures"):
                try:
                    i = filter(lambda x: x.type.startswith("image"), entry[key])
                    images |= set([item.href for item in i])
                except KeyError:
                    pass
            # from html content
            if article:
                if article["images"]:
                    images |= set(article["images"])

            # filter out some images
            entry["images"] = self.filter_images(images, minimum=(70,70))
            entry["image"] = entry["image"] or self.biggest_image(entry["images"])

            # get even more images from links in entry
            try:
                for link in entry["links"]:
                    try:
                        images |= sef.crawlHTML(soupparser.parse(self.cache[link]))["images"]
                    except:
                        pass
            except KeyError:
                pass # there were no links

            # give the images to the entry finally
            entry["images"] = set(images)
            entry["image"] = entry["image"] or self.biggest_image(entry["images"])

            # clean up content
            if article:
                entry["summary"] = article["content"]
        return feed

if __name__ == "__main__":
    import feedparser
    from os import execv
    from pprint import pprint as pp

    c = Crawler(PersistentCacher())
    #feed = feedparser.parse("http://www.reddit.com/r/aww/.rss")
    #feed = feedparser.parse("http://www.tigsource.com/feed/")
    feed = feedparser.parse("http://apod.nasa.gov/apod.rss")
    c.enrich(feed)
    pp(feed)
    #execv("/usr/bin/ristretto", filter(None, [entry["image"] for entry in feed["entries"]]))
