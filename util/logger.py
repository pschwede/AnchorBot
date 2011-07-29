import pprint

class Logger(object):
    def __init__(self, verbose=False, write=False):
        self.verbose = verbose
        self.pp = pprint.PrettyPrinter(indent=4)
        if verbose:
            self.log = self.__log_verbose
            if write:
                self.log = self.__log_verbose_write
        elif write:
            self.log = self.__log_nonverbose_write
        else:
            self.log = self.__log_nonverbose

    def __log_verbose(self, obj):
        pp.pprint(obj)
        f = open("/tmp/lyrebird.log", "a")
        f.write(str(obj)+"\n")
        f.close()

    def __log_nonverbose_write(self, obj):
        f = open("/tmp/lyrebird.log", "a")
        f.write(str(obj)+"\n")
        f.close()

    def __log_verbose_write(self, obj):
        pp.pprint(obj)
        f = open("/tmp/lyrebird.log", "a")
        f.write(str(obj)+"\n")
        f.close()

    def __log_nonverbose(self, obj):
        pass

def log(obj):
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(obj)
    f = open("/tmp/lyrebird.log", "a")
    f.write(str(obj)+"\n")
    f.close()

if __name__ == "__main__":
    log(dir(pprint))
