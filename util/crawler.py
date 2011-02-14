#!/usr/bin/env python

import urllib, re, mimetypes, os.path, Image

from storage import Cacher

"""
Follows redirections and delivers some useful functions for remote images.
"""

class Crawler(object):
    def __init__(self, proxies=None):
        self.opener = urllib.FancyURLopener(proxies)
        self.re_img = re.compile('(?<=<img src=").*(?=")', re.I)
        self.re_a = re.compile('(?<=href=").*(?=")', re.I)
        self.cache = Cacher() # for not retrieving things twice!

    def __load_file(self, url):
        if self.cache[url]:
            return self.cache[url]
        else:
            f = self.opener.retrieve(url)
            self.cache[url] = f
            return f

    def images(self, url, linked=False):
        f = self.opener.open(url)
        url = f.geturl()
        f.close()
        filetypes = ("jpg", "png","gif","jpeg")
        for typ in filetypes:
            if url.lower().endswith(typ):
                return [url]
        images = []
        f = self.__load_file(url)
        f = open(f[0], 'r')
        m = self.re_img.findall("\n".join(f.readlines()))
        for item in m:
            if not item.startswith(url[:4]):
               item = os.path.dirname(url)+"/"+item 
            images.append(item)
        f.close()
        if linked:
            for item in self.links(url):
                for typ in filetypes:
                    if item.lower().endswith(typ):
                        images = list(set(images+[item]))
        return images

    def compare_image(self, im1, im2):
        f = self.__load_file(im1)
        im = Image(open(f[0]))
        x1, y1 = im.size
        f = self.__open_file(im2)
        im = Image(open(f[1]))
        x2, y2 = im.size
        if x1*y1 < x2*y2:
            return -1
        elif x1*y1 == x2*y2:
            return 0
        return 1

    def biggest_image(self, imagelist, linked=False):
        biggest = None
        x, y = 0, 0
        for imgurl in imagelist:
            f = self.__load_file(imgurl)
            im = Image.open(f[0])
            if x*y < im.size[0]*im.size[1]:
                x, y = im.size
                biggest = imgurl
        return biggest

    def closest_image(self, imagelist, x, y):
        closest = None
        dx, dy = 10**10, 10**10
        for imgurl in imagelist:
            f = self.opener.retrieve(imgurl)
            im = Image.open(f[0])
            if dx/dy > abs(im.size[0]-x) / abs(im.size[1]-y):
                dx, dy = abs(im.size[0]-x), abs(im.size[1]-y)
                closest = imgurl
        return closest

    def links(self, url):
        links = []
        f = self.opener.open(url)
        url = f.geturl()
        f = self.__load_file(url)
        f = open(f[0], 'r')
        for item in self.re_a.findall("\n".join(f.readlines())):
            if not item.startswith(url[:4]):
                item = os.path.dirname(url)+"/"+item
            links.append(item)
        f.close()
        return links

if __name__ == "__main__":
    c = Crawler()
    print c.images("http://tinyurl.com/mn3vll")
    print c.images("http://apod.nasa.gov/apod/")
    print c.images("http://apod.nasa.gov/apod/ap110211.html", True)
    print c.links("http://apod.nasa.gov/apod/")
    print c.biggest_image(c.images("http://apod.nasa.gov/apod/ap110211.html"))
    print c.closest_image(c.images("http://apod.nasa.gov/apod/ap110211.html"), 400, 400)

