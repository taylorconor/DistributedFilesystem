"""
Replication Manager

"""

from utils.TCPServer import TCPServer
from utils.Constants import Response
from utils.ReplicationSet import ReplicationController
from utils.DirectoryTree import Location

class ReplicationManager():

    def _advertise_handler(self, conn, host, port):
        location = Location(host, port)
        self._replication_controller.add(location)
        conn.send(Response.OK)

    def _lookup_handler(self, conn, host, port):
        location = Location(host, port)
        set = self._replication_controller.lookup(location)
        set.remove(location)    # don't include the requesting node in the response, it already knows it's in the set
        str_set = ""            # a string representation of the response set
        for item in set:
            # convert each item in the response set to the string representation (easier to parse for the client)
            str_set += item.get_string() + " "
        conn.send(Response.OK + " " + str_set.rstrip(" "))

    def _request_handler(self, conn):
        try:
            # no initial request can be longer than 8096 bytes
            data = conn.recv(8096)
            input = data.split(" ")

            # invoke respective handlers for the input command
            if input[0] == "ADVERTISE":
                self._advertise_handler(conn, input[1], input[2])
                print "Received ADVERTISE from "+input[1]+":"+input[2]
            elif input[0] == "LOOKUP":
                self._lookup_handler(conn, input[1], input[2])
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
        self._server.start()
        self._replication_controller = ReplicationController()
