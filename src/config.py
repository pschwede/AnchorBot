#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import os
import threading
import time

import pickle

from logger import log

HOME = os.path.join(os.path.expanduser("~"), ".anchorbot")
DBPATH = os.path.join(HOME, "database.sqlite")
HERE = os.path.realpath(os.path.dirname(__file__))
TEMP = os.path.join(os.path.expanduser("~"), ".cache/anchorbot/")
HTML = os.path.join(HOME, "index.html")
__appname__ = "AnchorBot"
__version__ = "1.1"
__author__ = "spazzpp2"

class SelfRenewingLock(threading.Thread):
    def __init__(self, lockfile, dtime=5):
        super(SelfRenewingLock, self).__init__()
        self.lockfile = lockfile
        self.DTIME = dtime
        self.stopevent = threading.Event()
        self.daemon = True
        self.__locked = False

    def run(self):
        while not self.stopevent.is_set():
            f = open(self.lockfile, 'w')
            pickle.dump(time.time(), f)
            f.close()
            time.sleep(self.DTIME/2.1)

    def stop(self):
        self.stopevent.set()

    def locked(self):
        # check, if file old enough to be unused
        if os.path.exists(self.lockfile):
            f = open(self.lockfile, 'r')
            old = pickle.load(f)
            f.close()
            if (time.time() - old) <= self.DTIME:
                return True
        return False

    def free(self):
        while os.path.exists(self.lockfile):
            os.remove(self.lockfile)


class Config(object):
    def __init__(self, path, defaults=dict(), defaultabos=set(),
            verbose=False):
        self.verbose = verbose
        self.path = os.path.realpath(path)
        self.lockfile = os.path.join(self.path, "anchorlock")
        self.lock = SelfRenewingLock(self.lockfile)
        self.locked = self.lock.locked()
        if self.locked:
            raise Exception("%s detected." % self.lockfile)
        if not os.path.isdir(self.path):
            os.mkdir(self.path)
        self.lock.start()
        self.configfile = os.path.join(self.path, "config")
        self.abofile = os.path.join(self.path, "abos")
        if os.path.exists(self.abofile):
            f = open(self.abofile, 'r')
            self.abos = filter(lambda x: len(x), f.read().split("\n"))
            f.close()
            self.abos = list(set(self.abos))  # remove doubles
            if self.verbose:
                log(self.abos)
        else:
            self.abos = defaultabos
        if os.path.exists(self.configfile):
            self.read_config()
        else:
            self.config = defaults
            self.write_config()

    def read_config(self):
        f = open(self.configfile, 'r')
        self.config = pickle.load(f)
        f.close()

    def write_config(self):
        f = open(self.configfile, 'w')
        pickle.dump(self.config, f, -1)
        f.close()

    def set(self, name, value):
        self.config[name] = value

    def __setitem__(self, name, value):
        self.set(name, value)

    def __getitem__(self, name):
        return self.get(name)

    def get(self, name):
        try:
            return self.config[name]
        except KeyError:
            return None

    def add_abo(self, url):
        if url[:4] not in ["http"]:
            url = "http://%s" % url
        self.abos.add(url)
        self.write_abos()

    def get_abos(self):
        return self.abos

    def del_abo(self, url):
        self.abos.remove(url)
        self.write_abos()

    def write_abos(self):
        f = open(self.abofile, "w")
        for abo in self.abos:
            f.write("%s\n" % abo)
        f.close()

    def shutdown(self):
        if not self.locked:
            self.write_abos()
            self.write_config()
            self.lock.free()

if __name__ == "__main__":
    s = SelfRenewingLock("/tmp/testlock", 4)
    s.start()
    assert not s.locked()
    time.sleep(3)
    assert s.locked()
    time.sleep(1)
    assert s.locked()
    time.sleep(5)
    assert s.locked()
    s.free()
    assert not s.locked()
