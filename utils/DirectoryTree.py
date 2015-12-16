"""
DirectoryTree

Represents the DirectoryServer's database. Everything is stored as a tree structure made up of File and Directory
objects. Everything is stored in memory
"""

import threading


class Location:

    def __init__(self, host, port):
        self.host = host
        self.port = port

    def compare(self, other_loc):
        if self.host != other_loc.host or self.port != other_loc.port:
            return False
        return True


class File(object):

    def __init__(self, name, location):
        self.name = name
        self.location = [location]

    def add_location(self, new_loc):
        # add this location to the location list, if it's not already there
        for loc in self.location:
            if loc.compare(new_loc):
                return
        self.location.append(new_loc)

    def locations(self):
        tmp_loc = []
        for loc in self.location:
            tmp_loc.append(loc.host + ":" + loc.port)
        return tmp_loc


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
        self._root = Directory("", Location("", 0))
        self._lock = threading.Lock()

    def _add_item(self, Type, name, location, path):
        parent = self.find(path)
        # only add an item if it does not already exist in the structure
        child = parent.get_child(name)
        if child is None:
            parent.add_child(Type(name, location))
        # otherwise, add this location to the list of locations where this item can be found
        else:
            child.add_location(location)

    def _add_file(self, name, location, path):
        self._lock.acquire()
        self._add_item(File, name, location, path)
        self._lock.release()

    def _add_directory(self, name, location, path):
        self._lock.acquire()
        self._add_item(Directory, name, location, path)
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
        location = Location(host, port)
        if node is None:
            return
        for filename in filenames:
            self._add_file(filename, location, dirpath)
        for dirname in dirnames:
            self._add_directory(dirname, location, dirpath)

    def _r_pretty_print(self, node, level, path):
        for item in node.children:
            print str(' '*level) + item.name + ", " + path + " @ " + str(item.locations())
            if isinstance(item, Directory):
                new_path = path + item.name + "/"
                self._r_pretty_print(item, level+2, new_path)

    def pretty_print(self):
        print "\n*** PRINTING ENTIRE DIRECTORY STRUCTURE ***"
        print "/"   # represent the root directory with a slash
        self._r_pretty_print(self._root, 2, "/")
        print "*******************************************\n"

