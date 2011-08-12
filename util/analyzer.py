import multiprocessing as mp
from re import compile

class Analyzer(object):
    r_crop = compile("\W")
    def __init__(self, key="content", eid="link", rarity=xrange(2,99)):
        self.entryscore = {} # {word: (eid, cnt)}
        self.key, self.eid = key, eid
        self.keywords = {} # {word: score}
        self.num_entries = 0
        self.rarity = rarity

    def __crop(self, word):
        return u"".join(self.r_crop.split(word))

    def __climb_keyword(self, cnt, word, entry):
        """
        Increments countings concerning keywords and the entries they occur in.
        """
        word = self.__crop(word)
        try:
            if self.keywords[word][0]+cnt < len(self.rarity):
            # only add words that don't occure too often
                self.keywords[word] =  (
                        self.keywords[word][0] + cnt,
                        self.keywords[word][1] + [entry[self.eid]],
                        )
        except KeyError:
            self.keywords[word] = (cnt, [entry[self.eid]],)

    def __filter_keywords(self):
        """
        Filters out keywords that are too rare.
        """
        for word, score in self.keywords.items():
            if score < self.rarity[0]:
                del self.keywords[word]

    def __climb_escore(self, cnt, word, step, entry):
        try:
            if cnt > self.entryscore[word][1]:
                self.entryscore[word] = (entry[self.eid], 1.*cnt/step)
        except KeyError:
            self.entryscore[word] = (entry[self.eid], 1.*cnt/step)

    def get_keywords_of_article(self, entry):
        keyw = []
        for word, (eid, cnt) in self.entryscore.items():
            if eid == entry[self.eid]:
                keyw.append(word)
        return keyw

    def get_keywords_of_articles(self, entries=[]):
        """
        Checks a list of entries for reoccuring unique words and keeps them.
        Adds score and keywords to entries.
        Returns the most popular word.
        """
        # gather occuring words
        for entry in entries:
            self.add(entry)
        self.__filter_keywords()
        return self.keywords

    def add(self, entry):
        """
        Analyzes a dict's entry in key for statistics and reminds them.
        Does not filter keywords.
        Returns itself.
        """
        self.num_entries += 1
        ewords = entry[self.key].lower().split(" ")
        ewset, l = set(ewords), len(ewords)
        for word in ewset:
            cnt = ewords.count(word)
            self.__climb_keyword(cnt, word, entry)
            self.__climb_escore(cnt, word, (float(l)/self.num_entries), entry)
        return self

if __name__ == "__main__":
    """
    Some testings.
    """
    entries = [
            {"url":1, "content":"UFO in NY NY NY"},
            {"url":2, "content":"Fun with ufos"},
            {"url":3, "content":"How to live in NY"},
            {"url":4, "content":"Fun FUN fun NY NY"}
            ]
    a = Analyzer(eid="url",rarity=xrange(3,99))
    print a.get_keywords_of_articles(entries)
    a.add({"url":5, "content":"UFO in NY"})
    print a.entryscore
    print a.get_keywords_of_articles()
