import pprint

def log(obj):
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(obj)

if __name__ == "__main__":
    log(dir(pprint))
