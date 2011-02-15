import os

class Config(object):
    def __init__(self, path):
        self.path = os.path.realpath(path)
        if not os.path.isdir(self.path):
            os.mkdir(self.path)
        self.configfile = os.path.join(self.path, "config")
        print "config:", self.configfile
        self.abofile = os.path.join(self.path, "abos")
        print "abo:", self.abofile
        if os.path.exists(self.abofile):
            f = open(self.abofile, 'r')
            self.abos = set(filter(lambda x: x != '', f.read().split("\n")))
            print self.abos
            f.close()
        else:
            self.abos = set()
        if os.path.exists(self.configfile):
            # TODO read/write config
            pass
        else:
            self.config = dict()

    def set(self, name, value):
        self.config[name] = value

    def __setitem__(self, name, value):
        self.set(name, value)

    def get(self, name):
        try:
            return self.config[name]
        except KeyError:
            return None

    def add_abo(self, url):
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

    def __del__(self):
        self.write_abos()
