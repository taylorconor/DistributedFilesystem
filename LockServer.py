"""
LockServer.py

This is the lock server, which is an authority on the usage state of the files in the system (e.g. which files are
locked or unlocked, and by who). Clients using the filesystem should check the status of the file or directory they
wish to modify before they modify it, and obtain a lock if possible, otherwise wait for the lock to become available.
"""

import os
import sys

from utils.TCPServer import TCPServer
from utils.Constants import Response


class LockList:

    def __init__(self):
        self.list = []

    def add(self, file, host, port):
        self.list.append((file, host, port))

    def remove(self, file, host, port):
        for (ifile, ihost, iport) in self.list:
            if file == ifile and host == ihost and port == iport:
                self.list.remove((ifile, ihost, iport))
                return

    def check_file(self, file):
        for (ifile, ihost, iport) in self.list:
            if file == ifile:
                return (ihost, iport)
        return None


class LockServer:

    def _lock_handler(self, conn, host, port, f):
        status = self._lock_list.check_file(f)
        if status is None:
            self._lock_list.add(f, host, port)
            conn.send(Response.OK)
        elif status[0] == host and status[1] == port:
            conn.send(Response.OK)
        else:
            conn.send(Response.LOCK_TAKEN)

    def _unlock_handler(self, conn, host, port, f):
        status = self._lock_list.check_file(f)
        if status is None:
            conn.send(Response.LOCK_FREE)
        elif status[0] == host and status[1] == port:
            self._lock_list.remove(f, host, port)
            conn.send(Response.OK)
        else:
            conn.send(Response.LOCK_TAKEN)

    def _request_handler(self, conn):
        try:
            # no initial request can be longer than 8096 bytes
            data = conn.recv(8096)
            input = data.split(" ")

            # invoke respective handlers for the input command
            if input[0] == "LOCK":
                self._lock_handler(conn, input[1], input[2], input[3])
                print "Received LOCK from "+input[1]+":"+input[2]+" for: "+input[3]
            elif input[0] == "UNLOCK":
                self._unlock_handler(conn, input[1], input[2], input[3])
            else:
                conn.send("INVALID_COMMAND")
            conn.close()
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print exc_type.__name__ + " " + fname + ":" + str(exc_tb.tb_lineno) + " " + str(e)
            conn.send(Response.ERROR)
            conn.close()

    def __init__(self, port):
        self._port = port
        self._server = TCPServer(self._port, 10, self._request_handler)
        self._lock_list = LockList()
        self._server.start()
