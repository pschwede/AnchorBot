#!/usr/bin/env python

import urllib, re, mimetypes, os.path, Image
from urlparse import urljoin
from lxml.cssselect import CSSSelector
from lxml.html import make_links_absolute, soupparser

from storage import PersistentCacher
from logger import log

"""
Follows redirections and delivers some useful functions for remote images.
"""

class Crawler(object):
    re_cln = re.compile('((<img[^>]+>)|(<div>\s*</div>)|[\n\r])', re.I)

    def __init__(self, cacher, proxies=None, verbose=False):
        self.opener = urllib.FancyURLopener(proxies)
        self.cache = cacher # for not retrieving things twice!
        self.verbose = verbose

    def crawl(self, url, type="RSS"):
        """ Returns a set of articles found on url """
        type = type.lower()
        if "rss" in type:
            tree = soupparser.parse(open(self.cache[url], 'r'))
            return self.crawlRSS(tree)
        elif "html" in type:
            f = open(self.cache[url])
            f = make_links_absolute(f, url)
            tree = soupparser.parse("".join(f.readlines()))
            return self.crawlHTML(tree)
        elif "description" in type:
            tree = soupparser.fromstring(url)
            return self.crawlHTML(tree)
    
    def crawlHTML(self, tree, similarcontent=None, depth=0, baseurl=None):
        imagesel = CSSSelector("img")
        textsel = CSSSelector("div,span,p")
        content = similarcontent or ""
        if similarcontent:
            for elem in textsel(tree):
                if elem.text and similarcontent in elem.text:
                    content = elem.text
                    break;
        images = list(set([urljoin(baseurl,img.get("src") or img.attrib.values()[0]) for img in imagesel(tree)]))
        linksel = CSSSelector("a")
        for elem in linksel(tree):
            link = elem.get("href")
            if link and link[-4:] in (".png",".jpg",".gif","jpeg"):
                images.append(urljoin(baseurl, link))
        return {"images": list(images), "content": self.clean(content)}

    def crawlRSS(self, tree, depth=1, callback=lambda x,y:None):
        sel = CSSSelector("channel > link, feed > link")
        url = sel(tree)
        if url:
            origin = url[0].text or url[0].get("src")
        else:
            origin = ""

        articles = []
        sel = CSSSelector("entry, item")
        linksel = CSSSelector("link, url")
        titlesel = CSSSelector("title")
        imagesel = CSSSelector("image, thumbnail")
        descsel = CSSSelector("description, content")
        for item in sel(tree):
            title = titlesel(item)[0].text
            links = linksel(item)
            if links:
                url = links[0].text or links[0].get("href") or links[0].tail or links[0].attrib.values()[0]
            else:
                url = None
            images = list()
            for image in imagesel(item):
                links = linksel(image)
                if links:
                    images.append(links[0].text or links[0].tail) 
                if image.attrib:
                    images.append(image.get("src") or image.attrib.values()[0])
            content = descsel(item)[0].text if descsel(item) else None
            if content:
                if depth and url:
                    htmlarticle = self.crawlHTML(soupparser.parse(open(self.cache[url], 'r')), content, baseurl=url)
                else:
                    htmlarticle = self.crawlHTML(soupparser.fromstring(self.unescape(content)))
                content = self.clean(htmlarticle["content"])
                images += htmlarticle["images"]
            else:
                content = ""
            articles.append(
                    {
                        "url": url,
                        "title": title,
                        "images": filter(None, images),
                        "content": self.clean(content),
                        "origin": origin,
                        }
                    )

        return articles

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
                errors.append(self.cache[imgurl])
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
                pass #result.append(self.cache[imgurl])
        return result

    def clean(self, htmltext):
        return self.re_cln.sub("", htmltext)

    def enrich(self, feed):
        #TODO this glue can be dumped when database support is being added
        #TODO remove unwanted images
        articles = self.crawlRSS(soupparser.parse(self.cache[feed["url"]]))
        feed = {"entries": [], 
                "url": feed["url"],
                "feed": {
                    "title": feed["feed"]["title"],
                    }
                }
        for article in articles:
            feed["entries"].append(
                    {
                        "summary": article["content"],
                        "title": article["title"],
                        "images": article["images"],
                        "image": self.biggest_image(article["images"]),
                        "links": [{"href": article["url"]}]
                        }
                    )
        return feed

if __name__ == "__main__":

    def cb(stats):
        print "\r%.2f%% - %s" % (stats[0]*100, stats[1])

    c = Crawler(PersistentCacher())
    """articles = c.crawl("http://www.reddit.com/r/aww/.rss")
    images = []
    for article in articles:
        images += article["images"]
    images = c.filter_images(set(images), minimum=(100,100))
    if images:
        os.execv("/usr/bin/ristretto", images)"""

    articles = c.crawl("http://www.zockerperlen.de/rss-artikel.php")
    import pprint as pp
    pp.pprint(articles)
