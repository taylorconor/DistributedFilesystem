import os
import errno
import shutil

from utils.TCPServer import TCPServer


class Node(object):

    # remove any trailing slashes from the end of a directory path
    def _clean_path(self, path):
        while path.endswith('/'):
            path = path[:len(path)-1]
        return path

    # GET downloads a file to the client
    def _get_handler(self, conn, input):
        filename = self._dir + input
        if not os.path.isfile(filename):
            conn.send("NO_EXIST")
        else:
            f = open(filename, "rb")
            l = f.read(1024)
            while l:
                conn.send(l)
                l = f.read(1024)
            f.close()
            conn.shutdown(socket.SHUT_WR)
            conn.close()

    # PUT uploads a file (either adding a new file or overwriting an existing one)
    def _put_handler(self, conn, input):
        filepath = os.path.dirname(input)
        if not os.path.isdir(self._dir + filepath):
            conn.send("NO_EXIST")
        else:
            conn.send("OK")
            f = open(self._dir + input, "wb")
            l = conn.recv(1024)
            while l:
                f.write(l)
                l = conn.recv(1024)
            f.close()
            conn.send("OK")

    # MKDIR creates a directory in the node
    def _mkdir_handler(self, conn, input):
        newdir = self._clean_path(self._dir + input)
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

    # DELETE deletes a file or directory *recursively* in the node
    def _delete_handler(self, conn, input):
        object = self._clean_path(self._dir + input)
        if os.path.isdir(object):
            shutil.rmtree(object)
            conn.send("OK")
        elif os.path.isfile(object):
            os.remove(object)
            conn.send("OK")
        else:
            conn.send("NO_EXIST")

    # called whenever the server receives data
    def _request_handler(self, conn):
        try:
            # no initial request can be longer than 8096 bytes
            data = conn.recv(8096)
            input = data.split()

            # invoke respective handlers for the input command
            if input[0] == "GET":
                self._get_handler(conn, input[1])
            elif input[0] == "PUT":
                self._put_handler(conn, input[1])
            elif input[0] == "MKDIR":
                self._mkdir_handler(conn, input[1])
            elif input[0] == "DELETE":
                self._delete_handler(conn, input[1])
            else:
                conn.send("INVALID_COMMAND")
            conn.close()
        except Exception as e:
            conn.send("ERR")
            conn.close()

    def __init__(self, dir):
        self._dir = dir
        self._server = TCPServer(8001, 10, self._request_handler)
        self._server.start()