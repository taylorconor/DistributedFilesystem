import os
import errno
import shutil

from utils.TCPServer import TCPServer

class DirectoryServer:

    def _advertise_handler(self, conn, host, port):
        self._hosts[self._host_idx] = (host, port)
        self._host_idx += 1
        conn.send("OK")
        conn.recv()

    def _request_handler(self, conn):
        try:
            # no initial request can be longer than 8096 bytes
            data = conn.recv(8096)
            input = data.split()

            # invoke respective handlers for the input command
            if input[0] == "ADVERTISE":
                self._advertise_handler(conn, input[1], input[2])
            else:
                conn.send("INVALID_COMMAND")
            conn.close()
        except Exception as e:
            conn.send("ERR")
            conn.close()

    def __init__(self):
        self._hosts = []
        self._host_idx = 0
        self._server = TCPServer(8001, 10, self._request_handler)
        self._server.start()