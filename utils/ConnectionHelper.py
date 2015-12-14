"""
ConnectionHelper

Wrapper class for socket. It makes sending and receiving files and large amounts of data easier
"""

class ConnectionHelper:

    def __init__(self, conn):
        self._conn = conn

    def send(self, data):
        self._conn.send(data)

    def recv(self, size=-1):
        if size is not -1:
            return self._conn.recv(size)
        l = self._conn.recv(1024)
        while l:
            l = self._conn.recv(1024)
        return l

    def send_file(self, f):
        l = f.read(1024)
        while l:
            self._conn.send(l)
            l = f.read(1024)

    def recv_file(self, f):
        l = self._conn.recv(1024)
        while l:
            f.write(l)
            l = self._conn.recv(1024)

    def close(self):
        self._conn.close()

    def shutdown(self, method):
        self._conn.shutdown(method)
