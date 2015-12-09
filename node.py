import re, os, errno
from server import Server

class Node(object):

    # called whenever the server receives data
    def request_handler(self, conn):
        try:
            data = conn.recv(8096)
            input = data.split()
            if input[0] == "GET":
                filename = self._dir + input[1]
                if not os.path.isfile(filename):
                    conn.send("NO_EXIST")
                else:
                    conn.send("Handling GET request for file: " + input[1])

            elif input[0] == "PUT":
                filepath = os.path.dirname(input[1])
                if not os.path.isdir(self._dir + filepath):
                    conn.send("NO_EXIST")
                else:
                    conn.send("Handling PUT request for file: " + input[1])

            elif input[0] == "MKDIR":
                newdir = self._dir + input[1]
                # remove trailing slash, if any
                while newdir.endswith('/'):
                    newdir = newdir[:len(newdir)-1]
                basedir = os.path.dirname(newdir)
                if not os.path.isdir(basedir):
                    conn.send("NO_EXIST")
                else:
                    try:
	                    os.makedirs(newdir)
                    except Exception as e:
	                    if e.errno != errno.EEXIST:
		                    raise

            elif input[0] == "DELETE":
                filename = self._dir + input[1]
                if not os.path.isfile(filename):
                    conn.send("NO_EXIST")
                else:
                    conn.send("Handling DELETE request for file: " + input[1])

            else:
                conn.send("ERR")
            conn.close()
        except Exception as e:
            conn.send("ERR")
            conn.close()

    def __init__(self, dir):
        self._dir = dir
        self._server = Server(8001, 10, self.request_handler)
        self._server.start()