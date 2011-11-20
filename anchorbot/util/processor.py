# -*- encoding: utf-8 -*-

import Queue, threading
from multiprocessing import Process

# TODO apply actormodel

class Processor( object ):
    def __init__( self, number, fun, callback ):
        """ initializes a list of Download Threads and a Queue.Queue """
        self.number = number
        self.threads = []
        self.queue = Queue.Queue()
        self.running = True
        self.fun = fun
        self.callback = callback
        for _ in range( number ):
            self.__run_daemon( fun, callback )

    def __while_running( self, fun, callback=None ):
        """Method for download threads
           Setting self.running to False would stop them all.
        """
        while self.running:
            url = self.queue.get()
            fun( url, callback )
            self.queue.task_done()

    def __for_in( self, fun, argslist, callback=None ):
        for args in argslist:
            fun( args )

    def __run_daemon( self, fun, callback ):
        """run a downloader *without* caching"""
        t = threading.Thread( target=self.__while_running, args=( fun, callback, ) )
        t.daemon = True
        t.start()
        self.threads.append( t )

    def run_one( self, url, callback=None ):
        self.queue.put_nowait( url )
        if len( self.threads ) < self.number:
            self.__run_daemon( self.fun, callback ) # Careful with this, since they could get more and more here

    def run_threaded( self, fun, callback=None ):
        """simple threaded wrapper around a function that takes a callback"""
        t = threading.Thread( target=fun, args=( callback, ) )
        t.daemon = True
        t.start()

    def __run_process( self, args, lock ):
        lock.acquire()
        self.fun( args )
        lock.release()

    def map( self, fun, bunch, single=None, n=2 ):
        processes = list()
        # split up entries and start processes with a smaller set of entries.
        l = len( bunch )
        step = l / n or 1
        if l:
                if l > step:
                    if single:
                        for i in range( 0, l, step ):
                            p = Process( target=fun, args=( bunch[i:i + step], single, ) )
                            p.daemon = True
                            processes.append( p )
                    else:
                        for i in range( n ):
                            p = Process( target=fun, args=( bunch[i:i + step], ) )
                            p.daemon = True
                            processes.append( p )
                else:
                    if single:
                        p = Process( target=fun, args=( bunch[0], single, ) )
                        p.daemon = True
                        processes.append( p )
                    else:
                        p = Process( target=fun, args=( bunch[0], ) )
                        p.daemon = True
                        processes.append( p )
        [p.start() for p in processes]
        [p.join() for p in processes]
