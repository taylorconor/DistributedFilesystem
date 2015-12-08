from server import Server

class Node(object):

    def request_handler(self, conn):
        try:
            data = conn.recv(8096)
            print "request_handler: request="+data
            conn.send("Thanks!")
            conn.close()
        except e:
            conn.close()

    def __init__(self, dir):
        self._dir = dir
        self._server = Server(8001, 10, self.request_handler)
        self._server.start()