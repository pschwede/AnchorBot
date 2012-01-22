# -*- encoding: utf-8 -*-

import threading
from multiprocessing import Process
from Queue import Empty
from time import sleep

# TODO apply actormodel

class Thread(threading.Thread):
    def __init__(self, fun, queue, name="Thread"):
        threading.Thread.__init__(self)
        self.fun, self.queue, self.name = fun, queue, name

    def run(self):
        while True:
            try:
                item = self.queue.get(False)
                self.fun(*item)
                self.queue.task_done()
            except Empty:
                sleep(1)
