#!/usr/bin/env python

import urllib, re, mimetypes, os.path, Image
from urlparse import urljoin

from storage import PersistentCacher
from logger import log

"""
Follows redirections and delivers some useful functions for remote images.
"""

class Crawler(object):
    def __init__(self, cacher, proxies=None):
        self.opener = urllib.FancyURLopener(proxies)
        self.re_img = re.compile('((?<=<img src=["\'])[^"\']*(?=["\'])|(?<=<img src=["\'])[^"\']*(?=["\']))', re.I)
        self.re_a = re.compile('(?<=href=")[^"\']*(?=")', re.I)
        self.re_emb = re.compile('(?<=["\'])[^"\']+\.swf[^"\']*(?=["\'])', re.I)
        self.re_cln = re.compile('((<img[^>]+>)|(<div>\s*</div>))', re.I)
        self.cache = cacher # for not retrieving things twice!

    def images_on_webpage(self, url, linked=False):
        url = url.replace("\/","/")
        filetypes = ("jpg", "png","gif","jpeg")
        for typ in filetypes:
            if url.lower().split("?")[0].endswith(typ):
                return [url]
        images = []
        f = self.cache[url]
        f = open(f, 'r')
        m = self.re_img.findall("\n".join(f.readlines()))
        f.close()
        for item in m:        
            images.append(self.cache[urljoin(url, item)])
        if linked:
            for item in self.links(url):
                for typ in filetypes:
                    if item.lower().endswith(typ):
                        images += [urljoin(url, item)]
        return list(set(images))

    def images_in_htmltext(self, htmltext):
        images = []
        m = self.re_img.findall(htmltext) # images must be absolutely adressed!
        for item in m:
            images.append(self.cache[item])
        return images

    def embededs(self, url, linked=False, verbose=False):
        url = url.replace("\/","/")
        filetypes = ("swf")
        #quick copy&paste from above
        for typ in filetypes:
            if url.lower().endswith(typ):
                return [url]
        embeds = []
        f = self.cache[url]
        f = open(f, 'r')
        m = self.re_emb.findall("\n".join(f.readlines()))
        for item in m:        
            if len( item ) >= 4 and not item.startswith(str(url)[:4]):
               item = os.path.dirname(url)+"/"+item 
            embeds.append(self.cache[item])
        f.close()
        if linked:
            for item in self.links(url):
                for typ in filetypes:
                    if item.lower().endswith(typ):
                        embeds = list(set(embeds+[item]))
        if embeds and verbose:
            log("found embeds: "+ str(embeds))
        return embeds

    
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
        if errors:
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
        if errors:
            log("PIL: "+str(errors))
        return closest

    def links(self, url):
        url = url.replace("\/","/")
        links = []
        f = open(self.cache[url], 'r')
        for item in self.re_a.findall("\n".join(f.readlines())):
            if len( item ) >= 4 and not str(item).startswith(str(url)[:4]):
                item = os.path.dirname(url)+"/"+item
            links.append(item)
        f.close()
        return links

    def clean(self, htmltext):
        return self.re_cln.sub("", htmltext)

    def enrich(self, feed):
        is_tweet = True
        for entry in feed["entries"]:
            # make sure there is a entry[summary]
            try:
                entry["summary"]
            except KeyError:
                try:
                    entry["summary"] = entry["summary_detail"]["value"]
                except KeyError:
                    print "No summary could be found: ", entry["title"]
                    return entry
            is_tweet &= len(entry["summary"]) == 140
            # get images in feed
            entry["images"] = self.images_in_htmltext(entry["summary"])
            try:
                if entry["images"] is not []:
                    entry["images"] += self.images_on_webpage(entry["links"][0]["href"], True)
                    entry["image"] = self.biggest_image(entry["images"])
                else:
                    entry["images"] += self.images_on_webpage(entry["links"][0]["href"], True)
                entry["embededs"] = self.embededs(entry["links"][0]["href"])
                if entry["embededs"]:
                    entry["embeded"] = entry["embededs"][0]
                else:
                    entry["embeded"] = None
            except KeyError:
                print "No image and/or embed in ", entry["title"]
            # TODO Get more text from webpage
            # clean up the text
            entry["summary"] = self.clean(entry["summary"])
            entry["summary_detail"]["value"] = self.clean(entry["summary_detail"]["value"])

if __name__ == "__main__":
    c = Crawler(PersistentCacher())
    print c.images("http://tinyurl.com/mn3vll")
    print c.images("http://apod.nasa.gov/apod/")
    print c.images("http://apod.nasa.gov/apod/ap110211.html", True)
    print c.links("http://apod.nasa.gov/apod/")
    print c.biggest_image(c.images("http://apod.nasa.gov/apod/ap110211.html"))
    print c.closest_image(c.images("http://apod.nasa.gov/apod/ap110211.html"), 400, 400)

