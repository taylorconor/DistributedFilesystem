"""
DirectoryTree

Represents the DirectoryServer's database. Everything is stored as a tree structure made up of File and Directory
objects. Everything is stored in memory
"""

import threading


class Location:

    def __init__(self, diskloc, host, port):
        self.diskloc = diskloc
        self.host = host
        self.port = port


class File(object):

    def __init__(self, name, location):
        self.name = name
        self.location = location


class Directory(File):

    def __init__(self, name, location):
        super(self.__class__, self).__init__(name, location)
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
        self._root = Directory("", Location("", "", ""))
        self._lock = threading.Lock()

    def _add_item(self, Type, name, location):
        parent = self.find(location.diskloc)
        # only add an item if it does not already exist in the structure
        if parent.get_child(name) is None:
            parent.add_child(Type(name, location))

    def _add_file(self, name, location):
        self._lock.acquire()
        self._add_item(File, name, location)
        self._lock.release()

    def _add_directory(self, name, location):
        self._lock.acquire()
        self._add_item(Directory, name, location)
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
        location = Location(dirpath, host, port)
        if node is None:
            return
        for filename in filenames:
            self._add_file(filename, location)
        for dirname in dirnames:
            self._add_directory(dirname, location)

    def _r_pretty_print(self, node, level):
        for item in node.children:
            if item.location.diskloc == "":
                loc = "/"Switchi
            else:
                loc = item.location.diskloc
            print str(' '*level) + item.name + ", " + loc + " @ " + item.location.host + ":" + item.location.port
            if isinstance(item, Directory):
                self._r_pretty_print(item, level+2)

    def pretty_print(self):
        print "\n*** PRINTING ENTIRE DIRECTORY STRUCTURE ***"
        print "/"   # represent the root directory with a slash
        self._r_pretty_print(self._root, 2)
        print "*******************************************\n"

