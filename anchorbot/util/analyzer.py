from re import compile, UNICODE as re_u
from datamodel import get_session_from_new_engine, Keyword

class Analyzer( object ):
    r_crop = compile( "\W", re_u )
    def __init__( self, key="content", eid="link", rarity=( 0.001, 1. ), dbpath=None ):
        self.entryscore = {} # {word: (eid, cnt)}
        self.key, self.eid = key, eid
        self.keywords = {} # {word: score}
        self.popularity = {}
        self.num_entries = 0
        self.rarity = rarity
        self.dbpath = dbpath

    def __crop( self, word ):
        return u"".join( self.r_crop.split( word ) )

    def __climb_keyword( self, cnt, word, entry ):
        """
        Increments countings concerning keywords and the entries they occur in.
        """
        word = self.__crop( word )
        try:
            #only add words that don't occure too often
            #if float(self.keywords[word][0]+cnt)/(len(self.keywords)+1) < self.rarity[1]:
            self.keywords[word] = ( 
                    self.keywords[word][0] + cnt,
                    self.keywords[word][1] + [entry[self.eid]],
                    )
            self.popularity[self.keywords[word][0]] = entry[self.eid]
        except KeyError:
            self.keywords[word] = ( cnt, [entry[self.eid]], )

    def __filter_keywords( self ):
        """
        Filters out keywords that are too rare.
        """
        for word, score in self.keywords.items():
            if score[0] / len( self.keywords ) < self.rarity[0]:
                if self.dbpath:
                    s = get_session_from_new_engine(self.dbpath)
                    count = s.query(Keyword).filter(Keyword.clickcount > 0)
                    count = count.filter(Keyword.word == word).count()
                    s.close()
                if not count:
                    del self.keywords[word]

    def __climb_escore( self, cnt, word, step, entry ):
        try:
            #TODO probably check, which of the entries is prefered!
            if cnt >= self.entryscore[word][1]:
                self.entryscore[word] = ( entry[self.eid], 1. * cnt / step )
        except KeyError:
            self.entryscore[word] = ( entry[self.eid], 1. * cnt / step )

    def get_keywords_of_article( self, entry ):
        self.__filter_keywords()
        keyw = []
        for word, tupl in self.entryscore.items():
            if tupl[0] == entry[self.eid]:
                keyw.append( word )
        return keyw

    def get_keywords_of_articles( self, entries=[] ):
        """
        Checks a list of entries for reoccuring unique words and keeps them.
        Adds score and keywords to entries.
        Returns the most popular word.
        """
        # gather occuring words
        for entry in entries:
            self.add( entry )
        self.__filter_keywords()
        return self.keywords

    def add( self, entry ):
        """
        Analyzes a dict's entry in key for statistics and reminds them.
        Does not filter keywords.
        Returns itself.
        """
        self.num_entries += 1
        ewords = filter( lambda x: len( x ) > 1, map( self.__crop, entry[self.key].lower().split( " " ) ) )
        ewset, l = set( ewords ), len( ewords )
        for word in ewset:
            cnt = ewords.count( word )
            self.__climb_keyword( cnt, word, entry )
            self.__climb_escore( cnt, word, ( float( l ) / self.num_entries ), entry )
        return self

if __name__ == "__main__":
    """
    Some testings.
    """
    entries = [
            {"url":1, "content":"UFO in NY NY NY"},
            {"url":2, "content":"Fun with ufos"},
            {"url":3, "content":"How to live in NY"},
            {"url":4, "content":"Fun FUN fun - NY NY"},
            {"url":5, "content":"UFO in NY"},
            {"url":6, "content":"london riot"},
            {"url":7, "content":"update: london riot"},
            ]
    a = Analyzer( eid="url", rarity=( .001, 1. ) )
    for entry in entries:
        print a.get_keywords_of_articles()
        print a.entryscore
        a.add( entry )
    print a.entryscore
    print a.get_keywords_of_article( entries[-2] )
