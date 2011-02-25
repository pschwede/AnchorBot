import pprint

def log(obj):
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(obj)
    f = open("/tmp/lyrebird.log", "a")
    f.write(str(obj)+"\n")
    f.close()

if __name__ == "__main__":
    log(dir(pprint))
