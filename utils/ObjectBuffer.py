"""
ObjectBuffer.py

Manages a buffered list of files and directories (such as the pending Advertisement buffer). this helps to reduce the
amount of update traffic in the network by grouping multiple update requests into one large request.
"""
import os
from utils.Advertisement import Advertisement


class ObjectBuffer:

    # the type of object being added to the buffer
    class Type:
        file = 0
        directory = 1
        deleteFile = 2
        deleteDirectory = 3

    def __init__(self, cv):
        self._buf = []
        self._cv = cv

    def _add_dir(self, dirpath):
        for item in self._buf:
            if item.dirpath == dirpath:
                return
        parent = os.path.dirname(dirpath.strip('/'))
        child = dirpath
        if child.startswith(parent):
            child = child[len(parent):].strip('/')
        self._buf.append(Advertisement(parent, [child], []))
        self._buf.append(Advertisement(dirpath, [], []))

    def _add_file(self, filename):
        dirpath = os.path.dirname(filename)
        for item in self._buf:
            if item.dirpath == dirpath:
                item.add_filename(filename)
                return
        adv = Advertisement(dirpath, [], [filename.lstrip(dirpath).lstrip('/')])
        self._buf.append(adv)

    def _add_delete_file(self, delete_item):
        dirpath = os.path.dirname(delete_item)
        for item in self._buf:
            if item.dirpath == dirpath:
                item.add_delete(item)
                return
        adv = Advertisement(dirpath, [], [], [delete_item])
        self._buf.append(adv)

    def _add_delete_dir(self, delete_item):
        # search for a directory who has the directory to be deleted as a child.
        parent = os.path.dirname(delete_item.rstrip('/'))
        for item in self._buf:
            if item.dirpath == parent:
                item.add_delete(delete_item)
                return
        adv = Advertisement(parent, [], [], [delete_item])
        self._buf.append(adv)

    def add(self, item, type):
        if item not in self._buf:
            self._cv.acquire()
            if type == self.Type.file:
                self._add_file(item)
            elif type == self.Type.directory:
                self._add_dir(item)
            elif type == self.Type.deleteFile:
                self._add_delete_file(item)
            elif type == self.Type.deleteDirectory:
                self._add_delete_dir(item)
            self._cv.notify()
            self._cv.release()

    def is_empty(self):
        if self._buf:
            return False
        return True

    def get_all(self):
        return self._buf

    def clear(self):
        self._buf = []
