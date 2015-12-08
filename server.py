import thread, Queue, socket, sys, os, signal

class Server(object):

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
        thread.start_new(self._listen, ())

    # stop the listener threads by filling the connection queue with None (which the threads will interpret as kill)
    def stop(self):
        for _ in range(self._threads):
            self._queue.put(None)

    # initialise the thread pool
    def _createPool(self):
        for i in range(self._threads):
            t = thread.start_new(self._consumer, (i,))
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
            # call the callback in a new (detached) thread so this consumer can continue
            thread.start_new(self._callback, (conn,))