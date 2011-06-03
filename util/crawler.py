#!/usr/bin/env python

import urllib, re, mimetypes, os.path, Image
from urlparse import urljoin

from storage import PersistentCacher
from logger import log

"""
Follows redirections and delivers some useful functions for remote images.
"""

class Crawler(object):
    re_cln = re.compile('((<img[^>]+>)|(<div>\s*</div>))', re.I)
    re_img = re.compile('((?<=<img src=["\'])[^"\']*(?=["\'])|(?<=<img src=["\'])[^"\']*(?=["\']))', re.I)
    re_a = re.compile('((?<=href=["\'])[^"\']+(?=["\'])|(?<=<link>)[^<]+(?=</link>))', re.I)
    re_embed = re.compile('(?<=["\'])[^"\']+\.swf[^"\']*(?=["\'])', re.I)
    re_audio = re.compile('((?<=enclosure url=["\'])[^"\']+(mp3|flac|ogg|m3u)(?=")|(?<=<audio src=["\'])[^"\']+(?=["\']))', re.I)
    re_video = re.compile('(?<=<video src=["\'])[^<]+(mpg|avi|fla)[^"\'](?=["\'])', re.I)

    def __init__(self, cacher, proxies=None, verbose=False):
        self.opener = urllib.FancyURLopener(proxies)
        self.cache = cacher # for not retrieving things twice!
        self.verbose = verbose

    def unescape(self, text):
        text = text.replace("\/","/")
        text = text.replace("&quot;","\"")
        text = text.replace("&lt;","<")
        text = text.replace("&gt;",">")
        return text

    def find_on_webpage(self, url, regex=[re_img,], filetypes=("jpg", "png", "gif", "jpeg"), ignore=("swf", "fla"), recursive=0, verbose=False, callback=None):
        # restore escaped urls
        url = self.unescape(url)

        # return yourself, if you're of needed type
        for typ in filetypes:
            if url.lower().split("?")[0].endswith(typ):
                return [url]
        
        if verbose:
            print "Crawling %s %i-recursively" % (url, recursive)

        # recursively call this function with each contained link if recursive>0
        f = open(self.cache[url], 'r')
        text = self.unescape("\n".join(f.readlines()))
        f.close()
        return self.find(text, url, regex, filetypes, ignore, recursive, verbose, callback)

    def find(self, text, url=None, regex=[re_img], filetypes=("jpg", "png", "gif", "jpeg"), ignore=("swf", "fla"), recursive=0, verbose=False, callback=None):
        findings = []
        matches = []
        for r in regex:
            matches += r.findall(text)

        if url:
            if callback:
                for i in range(len(matches)):        
                    item = matches[i]
                    callback((float(i+1)/len(matches), item))
                    findings.append(urljoin(url, item))
            else:
                for item in matches:
                    findings.append(urljoin(url, item))
            links = self.links(url)
            if links and recursive > 0:
                for item in links:
                    findings += self.find_on_webpage(urljoin(url, item), regex, filetypes, ignore, recursive-1, verbose, callback)
        else:
            for item in matches:
                findings.append(self.cache[item])
        if findings and verbose:
            log("found: %s" % str(findings))
        return list(set(findings))

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
        for imgurl in set(images):
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

    def links(self, url):
        url = self.unescape(url)
        links = []
        f = open(self.cache[url], 'r')
        for item in self.re_a.findall(self.unescape("\n".join(f.readlines()))):
            if len( item ) >= 4 and not str(item).startswith(str(url)[:4]):
                item = urljoin(os.path.dirname(url), self.unescape(item))
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
                    if self.verbose:
                        log("No summary could be found: %s" % entry["title"])
                    return entry
            is_tweet &= len(entry["summary"]) == 140
            entry["images"] = []
            # get media from feed
            try:
                for encl in entry["enclosures"]:
                    if encl["type"].startswith("image"):
                        entry["images"] += [self.cache[encl["href"]]]
                    elif encl["type"].startswith("audio"):
                        entry["audio"] = encl["href"] # won't download
                    elif encl["type"].startswith("video"):
                        entry["video"] = encl["href"] # won't download
            except KeyError:
                pass
            entry["images"] += self.find(entry["summary"]) # searches for images in string by default
            try:
                for link in entry["links"]:
                    entry["images"] += self.find_on_webpage(link["href"], recursive=0)
                entry["image"] = self.biggest_image(entry["images"])
                """entry["embededs"] = self.find_on_webpage(entry["links"][0]["href"], regex=[self.re_embed], filetypes=("fla","swf"), recursive=0)
                if entry["embededs"]:
                    entry["embeded"] = entry["embededs"][0]
                else:
                    entry["embeded"] = None""" # ignore for now.. (may crash webkit)
            except KeyError:
                if self.verbose:
                    log("No image and/or embed in %s" % entry["title"])
            # TODO Get more text from webpage
            # clean up the text
            entry["images"] = self.filter_images(set(entry["images"]), minimum=(32,32))
            entry["summary"] = self.clean(entry["summary"])
            entry["summary_detail"]["value"] = self.clean(entry["summary_detail"]["value"])

if __name__ == "__main__":

    def cb(stats):
        print "\r%.2f%% - %s" % (stats[0]*100, stats[1])

    c = Crawler(PersistentCacher())
    imgs = c.find_on_webpage("http://reddit.com/r/aww/.rss", regex=[c.re_img, c.re_a], filetypes=("jpg","gif","jpeg","png"), recursive=0, callback=cb)
    imgs = c.filter_images(imgs, minimum=(100,100))
    if imgs:
        os.execv("/usr/bin/ristretto", imgs)

    """ audio = c.find_on_webpage("http://ws.audioscrobbler.com/2.0/user/spazzpp2/podcast.rss", regex=[c.re_audio], filetypes=("mp3","ogg","flac"), callback=cb)
    if audio:
        print "vlc", " ".join(audio)
        os.execv("/usr/bin/vlc", audio) """
