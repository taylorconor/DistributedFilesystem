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
                self._advertise_buffer.add(input, ObjectBuffer.Type.file)

    # MKDIR creates a directory in the node
    def _mkdir_handler(self, conn, input):
        newdir = str(self._dir + input.strip('/'))
        basedir = os.path.dirname(newdir)
        if not os.path.isdir(basedir):
            conn.send(Response.NO_EXIST)
        else:
            try:

                os.makedirs(newdir)
                conn.send(Response.OK)
                self._advertise_buffer.add(input.strip('/'), ObjectBuffer.Type.directory)
                # TODO: send to replication manager
            except Exception as e:
                if e.errno != errno.EEXIST:
                    raise
                else:
                    conn.send(Response.EXISTS)

    # DELETE deletes a file or directory *recursively* in the node
    def _delete_handler(self, conn, input):
        object = str(self._dir + input).rstrip('/')
        if os.path.isdir(object):
            shutil.rmtree(object)
            conn.send(Response.OK)
            self._advertise_buffer.add(input, ObjectBuffer.Type.deleteDirectory)
        elif os.path.isfile(object):
            os.remove(object)
            conn.send(Response.OK)
            self._advertise_buffer.add(input, ObjectBuffer.Type.deleteFile)
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

    def _init_advertise(self, server, host, port, adv_host, adv_port):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((adv_host, adv_port))
        except Exception as e:
            if e.errno == errno.ECONNREFUSED:
                print "*!* ERROR: Unable to connect to " + server + "!"
                print "*!* Node and " + server + " are *NOT* in sync!"
            else:
                print e
            return None
        s.send("ADVERTISE "+host+" "+str(port))
        data = s.recv(1024)
        if data != Response.OK:
            print "Received unusual response from " + server + ": " + data + ". Attempting to continue anyway."
        return s

    def _directory_server_advertisement(self, host, port, ds_host, ds_port):
        print "Advertising to Directory Server..."
        s = self._init_advertise("Directory Server", host, port, ds_host, ds_port)
        if s is None:
            return
        # repeatedly send advertisement messages of the structure of the server filesystem
        for (dirpath, dirnames, filenames) in os.walk(self._dir):
            advertisement = Advertisement(self._relative_path(self._dir, dirpath), dirnames, filenames)
            s.send(advertisement.toJSON())
            data = s.recv(1024)
            if data != Response.OK:
                print "Received unusual response from Directory Server: "+data+". Attempting to continue anyway."
        s.close()
        print "Advertisement complete: Node and Directory Server in sync."

    def _replication_manager_advertisement(self, host, port, rm_host, rm_port):
        print "Advertising to Replication Manager..."
        s = self._init_advertise("Replication Manager", host, port, rm_host, rm_port)
        if s is None:
            return
        s.close()
        print "Advertisement complete: Node and Replication Manager in sync."

    def _full_advertise(self, host, port, ds_host, ds_port, rm_host, rm_port):
        self._directory_server_advertisement(host, port, ds_host, ds_port)
        self._replication_manager_advertisement(host, port, rm_host, rm_port)

    def _incremental_advertise(self, host, port, ds_host, ds_port):
        while True:
            # sleep on condition variable
            while self._advertise_buffer.isEmpty():
                self._advertise_cv.acquire()
                self._advertise_cv.wait()
                self._advertise_cv.release()
                time.sleep(Interval.ADVERTISE)
            # if the pc reaches here, this thread has been woken to send an incremental advertise and clear the buffer
            s = self._init_advertise("Directory Server", host, port, ds_host, ds_port)
            if s is None:
                return
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

    def __init__(self, dir, host, port, ds_host, ds_port, rm_host, rm_port):
        self._dir = dir
        # append a slash to the end of the home directory if it's not passed in
        if self._dir[len(self._dir)-1] != '/':
            self._dir += '/'
        self._advertise_cv = threading.Condition()
        self._advertise_buffer = ObjectBuffer(self._advertise_cv)
        # do an initial full advertisement (to the directory server and replication manager) before the threadpool init
        self._full_advertise(host, port, ds_host, ds_port, rm_host, rm_port)
        # now initialise the node's listening threadpool with 10 threads
        self._server = TCPServer(port, 10, self._request_handler)
        t = threading.Thread(target=self._incremental_advertise, args=(host, port, ds_host, ds_port,))
        t.daemon = True
        t.start()
        self._server.start()
        print "Node server started successfully."
