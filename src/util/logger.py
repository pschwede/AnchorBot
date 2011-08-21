import pprint

"""
Logger class
============

* fast
* simple
* configurable
"""

class Logger( object ):
    def __init__( self, verbose=False, write="/tmp/lyrebird.log" ):
        self.verbose = verbose
        self.write = write
        self.pp = pprint.PrettyPrinter( indent=4 )

        # Choose strategy here! 
        # Assigning a method once is supposed to be faster than checking
        # the options in an if-statement every time it's called.
        if verbose:
            self.log = self.__log_verbose
            if write:
                self.log = self.__log_verbose_write
        elif write:
            self.log = self.__log_nonverbose_write
        else:
            self.log = self.__log_nonverbose

    def __log_verbose( self, obj ):
        self.pp.pprint( obj )
        f = open( self.write, "a" )
        f.write( str( obj ) + "\n" )
        f.close()

    def __log_nonverbose_write( self, obj ):
        f = open( self.write, "a" )
        f.write( str( obj ) + "\n" )
        f.close()

    def __log_verbose_write( self, obj ):
        self.pp.pprint( obj )
        f = open( self.write, "a" )
        f.write( str( obj ) + "\n" )
        f.close()

    def __log_nonverbose( self, obj ):
        pass

def log( obj ):
    pp = pprint.PrettyPrinter( indent=4 )
    pp.pprint( obj )
    f = open( "/tmp/lyrebird.log", "a" )
    f.write( str( obj ) + "\n" )
    f.close()

if __name__ == "__main__":
    log( dir( pprint ) )
