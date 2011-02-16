import os
try:
    import cpickle as pickle
except:
    import pickle

class Config(object):

    locked = False

    def __init__(self, path, defaults=dict(), defaultabos=set()):
        self.path = os.path.realpath(path)
        self.lockfile = os.path.join(self.path, "lock")
        self.locked = self.__locked()
        if self.locked:
            self.locked = True
            raise Exception
        else:
            f = open(self.lockfile, 'w')
            f.write("LOCK")
            f.close()
        if not os.path.isdir(self.path):
            os.mkdir(self.path)
        self.configfile = os.path.join(self.path, "config")
        self.abofile = os.path.join(self.path, "abos")
        if os.path.exists(self.abofile):
            f = open(self.abofile, 'r')
            self.abos = set(filter(lambda x: len(x)>0, f.read().split("\n")))
            print self.abos
            f.close()
        else:
            self.abos = defaultabos
        if os.path.exists(self.configfile):
            self.read_config()
        else:
            self.config = defaults
            self.write_config()

    def __locked(self):
        return self.locked or os.path.exists(self.lockfile)

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

    def quit(self):
        if not self.locked:
            self.write_abos()
            self.write_config()
            os.remove(self.lockfile)
