import os
import errno
import shutil
import json

from utils.TCPServer import TCPServer
from utils.DirectoryTree import DirectoryTree

class DirectoryServer:

    def _advertise_handler(self, conn, host, port):
        conn.send("OK")
        data = conn.recv(8096)
        while data:
            data = json.loads(data)
            self._tree.add(host, port, data["dirnames"], data["filenames"], data["dirpath"])
            conn.send("OK")
            data = conn.recv(8096)

    def _get_handler(self, conn, location):
        node = self._tree.find(location)
        if node is None:
            conn.send("NO_EXIST")
        else:
            conn.send(node.location)

    def _request_handler(self, conn):
        try:
            # no initial request can be longer than 8096 bytes
            data = conn.recv(8096)
            input = data.split(" ")

            # invoke respective handlers for the input command
            if input[0] == "ADVERTISE":
                self._advertise_handler(conn, input[1], input[2])
                print "Received ADVERTISE from "+input[1]+":"+input[2]
            if input[0] == "GET":
                self._get_handler(conn, input[1])
            # FOR TESTING ONLY
            elif input[0] == "PRINT":
                self._tree.pretty_print()
            else:
                conn.send("INVALID_COMMAND")
            conn.close()
        except Exception as e:
            print str(e)
            conn.send("ERR")
            conn.close()

    def __init__(self, port):
        self._port = port
        self._server = TCPServer(self._port, 10, self._request_handler)
        self._tree = DirectoryTree()
        self._server.start()