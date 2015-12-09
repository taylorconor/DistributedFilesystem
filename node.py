import re, os, errno, shutil
from server import Server

class Node(object):

    # remove any trailing slashes from the end of a directory path
    def _clean_path(self, path):
        while path.endswith('/'):
            path = path[:len(path)-1]
        return path

    # called whenever the server receives data
    def _request_handler(self, conn):
        try:
            data = conn.recv(8096)
            input = data.split()
            if input[0] == "GET":
                filename = self._dir + input[1]
                if not os.path.isfile(filename):
                    conn.send("NO_EXIST")
                else:
                    conn.send("Handling GET request for file: " + input[1])

            # PUT uploads a file (either adding a new file or overwriting an existing one)
            elif input[0] == "PUT":
                filepath = os.path.dirname(input[1])
                if not os.path.isdir(self._dir + filepath):
                    conn.send("NO_EXIST")
                else:
                    conn.send("OK")
                    f = open(self._dir + input[1], "wb")
                    l = conn.recv(1024)
                    while l:
                        f.write(l)
                        l = conn.recv(1024)
                    f.close()
                    conn.send("OK")

            elif input[0] == "MKDIR":
                newdir = self._clean_path(self._dir + input[1])
                basedir = os.path.dirname(newdir)
                if not os.path.isdir(basedir):
                    conn.send("NO_EXIST")
                else:
                    try:
                        os.makedirs(newdir)
                        conn.send("OK")
                    except Exception as e:
	                    if e.errno != errno.EEXIST:
		                    raise
                            else:
                                conn.send("EXISTS")

            elif input[0] == "DELETE":
                object = self._clean_path(self._dir + input[1])
                if os.path.isdir(object):
                    shutil.rmtree(object)
                    conn.send("OK")
                elif os.path.isfile(object):
                    os.remove(object)
                    conn.send("OK")
                else:
                    conn.send("NO_EXIST")

            else:
                conn.send("INVALID_COMMAND")
            conn.close()
        except Exception as e:
            conn.send("ERR")
            conn.close()

    def __init__(self, dir):
        self._dir = dir
        self._server = Server(8001, 10, self._request_handler)
        self._server.start()