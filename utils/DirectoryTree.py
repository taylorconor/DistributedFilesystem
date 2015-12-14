"""
DirectoryTree

Represents the DirectoryServer's database. Everything is stored as a tree structure made up of File and Directory
objects. Everything is stored in memory
"""

import threading

class File:

    def __init__(self, name, location, host, port):
        self.name = name
        self.location = location
        self.host = host
        self.port = port

class Directory:

    def __init__(self, name, location, host, port):
        self.name = name
        self.location = location
        self.host = host
        self.port = port
        self.children = []

    def get_child(self, name):
        for child in self.children:
            if child.name == name:
                return child
        return None

    def add_child(self, obj):
        self.children.append(obj)

class DirectoryTree:

    def __init__(self):
        # initialise the root directory, it has no name or location (it's
        # not stored anywhere, it's fragmented across multiple nodes)
        self._root = Directory("", "", "", 0)
        self._lock = threading.Lock()

    def _add_item(self, Type, name, location, host, port):
        parent = self.find(location)
        # only add an item if it does not already exist in the structure
        if parent.get_child(name) is None:
            parent.add_child(Type(name, location, host, port))

    def _add_file(self, name, location, host, port):
        self._lock.acquire()
        self._add_item(File, name, location, host, port)
        self._lock.release()

    def _add_directory(self, name, location, host, port):
        self._lock.acquire()
        self._add_item(Directory, name, location, host, port)
        self._lock.release()

    def find(self, path):
        path = path.strip('/').split('/')
        node = self._root
        for item in path:
            tnode = node.get_child(item)
            if tnode is not None:
                node = tnode
        return node

    def add(self, host, port, dirnames, filenames, dirpath):
        node = self.find(dirpath)
        if node is None:
            return
        for filename in filenames:
            self._add_file(filename, dirpath, host, port)
        for dirname in dirnames:
            self._add_directory(dirname, dirpath, host, port)

    def _r_pretty_print(self, node, level):
        for item in node.children:
            print str(' '*level) + item.name + ", " + item.location + " @ " + item.host + ":" + item.port
            if isinstance(item, Directory):
                self._r_pretty_print(item, level+2)

    def pretty_print(self):
        print "\n*** PRINTING ENTIRE DIRECTORY STRUCTURE ***"
        print "/"   # represent the root directory with a slash
        self._r_pretty_print(self._root, 2)
        print "*******************************************\n"

