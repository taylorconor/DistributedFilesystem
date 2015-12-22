"""
Node

An ordinary node server
"""

import os
import errno
import shutil
import socket
import threading
import time

from utils.TCPServer import TCPServer
from utils.Constants import Response, Interval
from utils.ObjectBuffer import ObjectBuffer
from utils.Advertisement import Advertisement


class Node(object):

    # convert a fully qualified path to a relative path
    def _relative_path(self, base, path):
        _base = base.strip('/')
        _path = path.strip('/')
        if _path.startswith(_base):
            _path = _path[len(_base):]
        return _path.strip('/')

    # GET downloads a file to the client
    def _get_handler(self, conn, input):
        filename = self._dir + input
        if not os.path.isfile(filename):
            conn.send(Response.NO_EXIST)
        else:
            f = open(filename, "rb")
            conn.send_file(f)
            f.close()
            conn.shutdown(socket.SHUT_WR)
            conn.close()

    # PUT uploads a file (either adding a new file or overwriting an existing one)
    def _put_handler(self, conn, input):
        filepath = os.path.dirname(input)
        if not os.path.isdir(self._dir + filepath):
            conn.send(Response.NO_EXIST)
        else:
            conn.send(Response.OK)
            # check if the file existed or not before overwriting
            exists = os.path.isfile(self._dir + input)
            f = open(self._dir + input, "wb")
            conn.recv_file(f)
            f.close()
            conn.send(Response.OK)

            # TODO: send to replication manager
            if not exists:
                self._advertise_buffer.add(input)

    # MKDIR creates a directory in the node
    def _mkdir_handler(self, conn, input):
        newdir = str(self._dir + input).strip('/')
        basedir = os.path.dirname(newdir)
        if not os.path.isdir(basedir):
            conn.send(Response.NO_EXIST)
        else:
            try:
                os.makedirs(newdir)
                conn.send(Response.OK)
                self._advertise_buffer.add(input.strip('/'), False)
                # TODO: send to replication manager
            except Exception as e:
                if e.errno != errno.EEXIST:
                    raise
                else:
                    conn.send(Response.EXISTS)

    # DELETE deletes a file or directory *recursively* in the node
    def _delete_handler(self, conn, input):
        object = str(self._dir + input).strip('/')
        if os.path.isdir(object):
            shutil.rmtree(object)
            conn.send(Response.OK)
        elif os.path.isfile(object):
            os.remove(object)
            conn.send(Response.OK)
        else:
            conn.send(Response.NO_EXIST)

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
                conn.send(Response.INVALID_COMMAND)
            conn.close()
        except Exception as e:
            conn.send(Response.ERROR + " " + str(e))
            conn.close()

    def _advertise_data(self, host, port, ds_host, ds_port):
        print "Advertising to Directory Server..."
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((ds_host, ds_port))
        except Exception as e:
            if e.errno == errno.ECONNREFUSED:
                print "*!* ERROR: Unable to connect to Directory Server!"
                print "*!* Node and Directory Server are *NOT* in sync!"
            else:
                print e
            return
        s.send("ADVERTISE "+host+" "+str(port))
        data = s.recv(1024)
        if data != Response.OK:
            print "Received unusual response from Directory Server: "+data+". Attempting to continue anyway."
        # repeatedly send advertisement messages of the structure of the server filesystem
        for (dirpath, dirnames, filenames) in os.walk(self._dir):
            advertisement = Advertisement(self._relative_path(self._dir, dirpath), dirnames, filenames)
            s.send(advertisement.toJSON())
            data = s.recv(1024)
            if data != Response.OK:
                print "Received unusual response from Directory Server: "+data+". Attempting to continue anyway."
        s.close()
        print "Advertisement complete: Node and Directory Server in sync."

    def _incremental_advertise(self, host, port, ds_host, ds_port):
        while True:
            # sleep on condition variable
            self._advertise_cv.acquire()
            while self._advertise_buffer.isEmpty():
                self._advertise_cv.wait()
                self._advertise_cv.release()
                time.sleep(Interval.ADVERTISE)
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                s.connect((ds_host, ds_port))
            except Exception as e:
                if e.errno == errno.ECONNREFUSED:
                    print "*!* ERROR: Unable to connect to Directory Server!"
                    print "*!* Node and Directory Server are *NOT* in sync!"
                else:
                    print e
                return
            s.send("ADVERTISE "+host+" "+str(port))
            data = s.recv(1024)
            if data != Response.OK:
                print "Received unusual response from Directory Server: "+data+". Attempting to continue anyway."
            self._advertise_cv.acquire()
            messages = self._advertise_buffer.getAllAdvertisements()
            for message in messages:
                s.send(message.toJSON())
                data = s.recv(1024)
                if data != Response.OK:
                    print "Received unusual response from Directory Server: "+data+". Attempting to continue anyway."
            self._advertise_buffer.clear()
            self._advertise_cv.release()
            s.close()
            print "Advertisement complete: Node and Directory Server in sync."

    def __init__(self, dir, host, port, ds_host, ds_port):
        self._dir = dir
        self._advertise_cv = threading.Condition()
        self._advertise_buffer = ObjectBuffer(self._advertise_cv)
        # do an initial (full) advertisement before the node is fully set up
        self._advertise_data(host, port, ds_host, ds_port)
        self._server = TCPServer(port, 10, self._request_handler)
        t = threading.Thread(target=self._incremental_advertise, args=(host, port, ds_host, ds_port,))
        t.daemon = True
        t.start()
        self._server.start()
        print "Node server started successfully."
