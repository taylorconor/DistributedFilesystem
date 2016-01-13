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
from utils.DirectoryTree import Location
from utils.ConnectionHelper import ConnectionHelper


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

    # XPUT uploads a file (either adding a new file or overwriting an existing one) WITHOUT forwarding it to the
    # replication set. this is used to stop PUT messages circling through the network forever
    def _xput_handler(self, conn, input):
        filepath = os.path.dirname(input)
        if not os.path.isdir(self._dir + filepath):
            conn.send(Response.NO_EXIST)
            return False
        conn.send(Response.OK)
        # check if the file existed or not before overwriting
        exists = os.path.isfile(self._dir + input)
        f = open(self._dir + input, "wb")
        conn.recv_file(f)
        f.close()
        conn.send(Response.OK)
        if not exists:
            self._advertise_buffer.add(input, ObjectBuffer.Type.file)
        return True

    # PUT uploads a file (either adding a new file or overwriting an existing one)
    def _put_handler(self, conn, input):
        # perform the usual replication-less xput first
        success = self._xput_handler(conn, input)
        # now add this put operation to the replication buffer if it was a successful xput (ie the client didn't try
        # to put a file to an invalid directory)
        if success:
            self._replication_buffer.add(input, ObjectBuffer.Type.file)

    # XMKDIR creates a directory in the node WITHOUT forwarding it to the replication set
    def _xmkdir_handler(self, conn, input):
        newdir = str(self._dir + input.strip('/'))
        basedir = os.path.dirname(newdir)
        if not os.path.isdir(basedir):
            conn.send(Response.NO_EXIST)
            return False
        else:
            try:
                os.makedirs(newdir)
                conn.send(Response.OK)
                self._advertise_buffer.add(input.strip('/'), ObjectBuffer.Type.directory)
                return True
            except Exception as e:
                if e.errno != errno.EEXIST:
                    raise
                else:
                    conn.send(Response.EXISTS)
                return False

    # MKDIR creates a directory in the node
    def _mkdir_handler(self, conn, input):
        success = self._xmkdir_handler(conn, input)
        if success:
            self._replication_buffer.add(input.strip('/'), ObjectBuffer.Type.directory)

    # XDELETE deletes a file or directory *recursively* in the node WITHOUT forwarding it to the replication set
    def _xdelete_handler(self, conn, input):
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
            return False
        return True

    #DELETE deletes a file or directory recursively
    def _delete_handler(self, conn, input):
        success = self._xdelete_handler(conn, input)
        if success:
            isfile = os.path.isfile(self._dir + input)
            repl_type = ObjectBuffer.Type.deleteFile if isfile else ObjectBuffer.Type.deleteDirectory
            self._replication_buffer.add(input, repl_type)

    # called whenever the server receives data
    def _request_handler(self, conn):
        try:
            # no initial request can be longer than 8096 bytes
            data = conn.recv(8096)
            input = data.split()

            # invoke respective handlers for the input command
            if input[0] == "GET":
                self._get_handler(conn, input[1])
            elif input[0] == "XPUT":
                self._xput_handler(conn, input[1])
            elif input[0] == "PUT":
                self._put_handler(conn, input[1])
            elif input[0] == "XMKDIR":
                self._xmkdir_handler(conn, input[1])
            elif input[0] == "MKDIR":
                self._mkdir_handler(conn, input[1])
            elif input[0] == "XDELETE":
                self._xdelete_handler(conn, input[1])
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
            s.send(advertisement.to_json())
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
            while self._advertise_buffer.is_empty():
                self._advertise_cv.acquire()
                self._advertise_cv.wait()
                self._advertise_cv.release()
                time.sleep(Interval.ADVERTISE)
            # if the pc reaches here, this thread has been woken to send an incremental advertise and clear the buffer
            s = self._init_advertise("Directory Server", host, port, ds_host, ds_port)
            if s is None:
                return
            self._advertise_cv.acquire()
            messages = self._advertise_buffer.get_all()
            for message in messages:
                s.send(message.to_json())
                data = s.recv(1024)
                if data != Response.OK:
                    print "Received unusual response from Directory Server: "+data+". Attempting to continue anyway."
            self._advertise_buffer.clear()
            self._advertise_cv.release()
            s.close()
            print "Advertisement complete: Node and Directory Server in sync."

    def _get_replication_set(self, host, port, rm_host, rm_port):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((rm_host, rm_port))
        except Exception as e:
            if e.errno == errno.ECONNREFUSED:
                print "*!* ERROR: Unable to connect to ReplicationManager!"
                print "*!* Node and ReplicationManager are *NOT* in sync!"
            else:
                print e
            return None
        s.send("LOOKUP "+host+" "+str(port))
        data = s.recv(1024)
        s.close()
        if len(data):
            arr = data.split(" ")[1:]   # remove the first element ("OK"), the rest of the elements are the replicants
            locations = []
            for item in arr:
                parts = item.split(":")
                loc = Location(parts[0], parts[1])
                locations.append(loc)
            return locations
        return None

    def _replication_manager_update(self, host, port, rm_host, rm_port):
        while True:
            # sleep on condition variable
            while self._replication_buffer.is_empty():
                self._replication_cv.acquire()
                self._replication_cv.wait()
                self._replication_cv.release()
                time.sleep(Interval.ADVERTISE)
            self._replication_cv.acquire()
            # flush the buffer and then release the lock so request handler threads waiting on the lock can continue
            adv_list = self._replication_buffer.get_all()
            self._replication_buffer.clear()
            self._replication_cv.release()

            # get the replication set
            set = self._get_replication_set(host, port, rm_host, rm_port)
            if set is None:
                continue

            for loc in set:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((loc.host, int(loc.port)))
                conn = ConnectionHelper(s)
                for item in adv_list:
                    print "ADV: dirpath="+str(item.dirpath)+", dirnames="+str(item.dirnames)+", filenames="+str(item.filenames)+", deletelist="+str(item.deletelist)
                    for dir in item.dirnames:
                        s.send("XMKDIR "+dir)
                        data = s.recv(1024)
                        if data != Response.OK:
                            print "Received unusual response from replication peer "+loc.host+":"+loc.port
                    for file in item.filenames:
                        s.send("XPUT "+file)
                        data = s.recv(1024)
                        if data != Response.OK:
                            print "Received unusual response from replication peer "+loc.host+":"+loc.port
                            continue    # abort XPUT operation
                        f = open(self._dir + item.dirpath + "/" + file, "rb")
                        conn.send_file(f)
                    for i in item.deletelist:
                        s.send("XDELETE "+i)
                        data = s.recv(1024)
                        if data != Response.OK:
                            print "Received unusual response from replication peer "+loc.host+":"+loc.port
                conn.close()

    def __init__(self, dir, host, port, ds_host, ds_port, rm_host, rm_port):
        self._dir = dir
        # append a slash to the end of the home directory if it's not passed in
        if self._dir[len(self._dir)-1] != '/':
            self._dir += '/'
        # initialise the condition variable and buffer for the incremental advertise thread
        self._advertise_cv = threading.Condition()
        self._advertise_buffer = ObjectBuffer(self._advertise_cv)
        # initialise the condition variable and buffer for the replication forwarder
        self._replication_cv = threading.Condition()
        self._replication_buffer = ObjectBuffer(self._replication_cv)
        # do an initial full advertisement (to the directory server and replication manager) before the threadpool init
        self._full_advertise(host, port, ds_host, ds_port, rm_host, rm_port)
        # now initialise the node's listening threadpool with 10 threads
        self._server = TCPServer(port, 10, self._request_handler)
        t = threading.Thread(target=self._incremental_advertise, args=(host, port, ds_host, ds_port,))
        t.daemon = True
        t.start()
        t = threading.Thread(target=self._replication_manager_update, args=(host, port, rm_host, rm_port,))
        t.daemon = True
        t.start()
        self._server.start()
        print "Node server started successfully."
