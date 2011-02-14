

class Analyzer(object):
    def __init__(self):
        self.entries = []
        self.occ = {}

    def add(self, obj):
        if type(obj) is list and type(obj[0]) is dict:
            self.entries += obj
        elif type(entries) is dict:
            self.entries.append(obj)

    def __build_occurance(self, entry):
        words = map(str.lower, entry["title"].split(" ")) #TODO
        for word in words:
            l = len(words)
            occ = float(words.count(word))/l
            if occ != 0:
                try:
                    self.occ[word][self.entries.index(entry)] = occ
                except KeyError:
                    self.occ[word] = {self.entries.index(entry): occ}

    def __sum(self):
        sums = {}
        for word in self.occ:
            for key,val in self.occ[word].items():
                try:
                    sums[word] = (sums[word][0]+val, key)
                except KeyError:
                    sums[word] = (val, key)
        return sorted(sums.items(), key=lambda x: x[1][0], reverse=True)
    
    def analyze(self, upper=1, lower=0):
        for entry in self.entries:
            self.__build_occurance(entry)
        sums = self.__sum()
        done = []
        for s in sums:
            if s[1][1] not in done and s[1][0] < upper and s[1][0] > lower:
                print self.entries[s[1][1]]
                done.append(s[1][1])

if __name__ == "__main__":
    entries = [{"title":"UFO in NY"},{"title":"Fun with ufos"},{"title": "How to live in NY"}, {"title":"Fun FUN fun NY NY"}]
    a = Analyzer()
    a.add(entries)
    a.analyze()
