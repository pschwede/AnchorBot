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
        self.re_img = re.compile('(?<=<img src=["\'])[^"\']*(?=["\'])', re.I)
        self.re_a = re.compile('(?<=href=").*(?=")', re.I)
        self.re_emb = re.compile('(?<=["\'])[^"\']+\.swf[^"\']*(?=["\'])', re.I)
        self.cache = cacher # for not retrieving things twice!

    def absolutize(self, base_url, relative_url):
        return urljoin(base_url, relative_url)

    def images(self, url, linked=False):
        filetypes = ("jpg", "png","gif","jpeg")
        for typ in filetypes:
            if url.lower().endswith(typ):
                return [url]
        images = []
        f = self.cache[url]
        f = open(f, 'r')
        m = self.re_img.findall("\n".join(f.readlines()))
        for item in m:        
            images.append(self.cache[self.absolutize(url, item)])
        f.close()
        if linked:
            for item in self.links(url):
                for typ in filetypes:
                    if item.lower().endswith(typ):
                        images += [self.absolutize(url, item)]
        return list(set(images))

    def embededs(self, url, linked=False):
        filetypes = ("swf")
        #quick copy&paste from above
        for typ in filetypes:
            if url.lower().endswith(typ):
                return [url]
        images = []
        f = self.cache[url]
        f = open(f, 'r')
        m = self.re_emb.findall("\n".join(f.readlines()))
        for item in m:        
            if not item.startswith(url[:4]):
               item = os.path.dirname(url)+"/"+item 
            images.append(self.cache[item])
        f.close()
        if linked:
            for item in self.links(url):
                for typ in filetypes:
                    if item.lower().endswith(typ):
                        images = list(set(images+[item]))
        if images:
            log("found embeds: "+ str(images))
        return images

    
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
        for imgurl in imagelist:
            try:
                im = Image.open(self.cache[imgurl])
            except IOError:
                log("Couldn't open %s" % self.cache[imgurl])
                return biggest
            imgurl = self.cache[imgurl]
            if x*y < im.size[0]*im.size[1]:
                x, y = im.size
                biggest = imgurl
        return biggest

    def closest_image(self, imagelist, x, y):
        closest = None
        dx, dy = 10**10, 10**10
        for imgurl in imagelist:
            im = Image.open(self.cache[imgurl])
            if dx/dy > abs(im.size[0]-x) / abs(im.size[1]-y):
                dx, dy = abs(im.size[0]-x), abs(im.size[1]-y)
                closest = imgurl
        return closest

    def links(self, url):
        links = []
        f = open(self.cache[url], 'r')
        for item in self.re_a.findall("\n".join(f.readlines())):
            if not item.startswith(url[:4]):
                item = os.path.dirname(url)+"/"+item
            links.append(item)
        f.close()
        return links

    def enrich(self, entry):
        try:
            entry["images"] = self.images(entry["links"][0]["href"], True)
            entry["image"] = self.biggest_image(entry["images"])
            entry["embededs"] = self.embededs(entry["links"][0]["href"])
            if entry["embededs"]:
                entry["embeded"] = entry["embededs"][0]
            else:
                entry["embeded"] = None
        except KeyError:
            log( entry)
        return entry
        

if __name__ == "__main__":
    c = Crawler(PersistentCacher())
    print c.images("http://tinyurl.com/mn3vll")
    print c.images("http://apod.nasa.gov/apod/")
    print c.images("http://apod.nasa.gov/apod/ap110211.html", True)
    print c.links("http://apod.nasa.gov/apod/")
    print c.biggest_image(c.images("http://apod.nasa.gov/apod/ap110211.html"))
    print c.closest_image(c.images("http://apod.nasa.gov/apod/ap110211.html"), 400, 400)

