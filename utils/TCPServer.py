import threading
import Queue
import socket
import sys
import os
import signal

from utils.ConnectionHelper import ConnectionHelper

class TCPServer(object):

    _queue = Queue.Queue()  # incoming connection queue
    _pool = []              # thread pool
    _host = "0.0.0.0"       # listen for all incoming connections

    def __init__(self, port, threads, callback):
        self._port = port
        self._threads = threads
        self._callback = callback
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # start the entire server
    def start(self):
        self._bind()
        self._createPool()
        # run the listener in a new (detached) thread
        t = threading.Thread(target=self._listen, args=())
        t.daemon = True
        t.start()

    # stop the listener threads by filling the connection queue with None (which the threads will interpret as kill)
    def stop(self):
        for _ in range(self._threads):
            self._queue.put(None)

    # initialise the thread pool
    def _createPool(self):
        for i in range(self._threads):
            t = threading.Thread(target=self._consumer, args=(i,))
            t.daemon = True
            t.start()
            self._pool.append(t)

    # bind socket to port
    def _bind(self):
        try:
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._socket.bind((self._host, self._port))
        except socket.error as err:
            raise Exception("Error "+str(err[0])+", bind failed: "+err[1])

    # listen for connections
    def _listen(self):
        self._socket.listen(10)
        while True:
            conn, addr = self._socket.accept()
            self._queue.put((conn, addr), False)

    # consume an item from the queue
    def _consumer(self, cid):
        waiting = True
        while waiting:
            v = self._queue.get()
            if v == None:
                break

            conn, addr = v
            conn_obj = ConnectionHelper(conn)
            # call the callback in a new (detached) thread so this consumer can continue
            t = threading.Thread(target=self._callback, args=(conn_obj,))
            t.daemon = True
            t.start()