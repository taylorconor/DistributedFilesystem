import os
import errno
import shutil
import json

from utils.Constants import Response
from utils.TCPServer import TCPServer
import utils.DirectoryTree as DT

class DirectoryServer:

    def _advertise_handler(self, conn, host, port):
        conn.send(Response.OK)
        data = conn.recv(8096)
        while data:
            data = json.loads(data)
            self._tree.add(host, port, data["dirnames"], data["filenames"], data["dirpath"])
            conn.send(Response.OK)
            data = conn.recv(8096)

    def _get_handler(self, conn, location):
        node = self._tree.find(location)
        if node is None:
            conn.send(Response.NO_EXIST)
        elif isinstance(node, DT.Directory):
            conn.send(Response.IS_DIRECTORY)
        else:
            conn.send(str(node.locations())+" "+location)

    def _put_handler(self, conn, location):
        pass
    def _mkdir_handler(self, conn, location):
        pass
    def _list_handler(self, conn, location):
        node = self._tree.find(location)
        if node is None:
            conn.send(Response.NO_EXIST)
        elif not isinstance(node, DT.Directory):
            conn.send(Response.CANT_LIST)
        else:
            children = []
            for child in node.children:
                children.append(child.name)
            conn.send(str(children))

    def _request_handler(self, conn):
        try:
            # no initial request can be longer than 8096 bytes
            data = conn.recv(8096)
            input = data.split(" ")

            # invoke respective handlers for the input command
            if input[0] == "ADVERTISE":
                self._advertise_handler(conn, input[1], input[2])
                print "Received ADVERTISE from "+input[1]+":"+input[2]
            elif input[0] == "GET":
                self._get_handler(conn, input[1])
            elif input[0] == "PUT":
                self._put_handler(conn, input[1])
            elif input[0] == "MKDIR":
                self._mkdir_handler(conn, input[1])
            elif input[0] == "LIST":
                self._list_handler(conn, input[1])
            # FOR TESTING ONLY
            elif input[0] == "PRINT":
                self._tree.pretty_print(input[1])
            else:
                conn.send("INVALID_COMMAND")
            conn.close()
        except Exception as e:
            print str(e)
            conn.send(Response.ERROR)
            conn.close()

    def __init__(self, port):
        self._port = port
        self._server = TCPServer(self._port, 10, self._request_handler)
        self._tree = DT.DirectoryTree()
        self._server.start()