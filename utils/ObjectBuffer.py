"""
ObjectBuffer

Manages a buffered list of files and directories (such as the pending Advertisement buffer)
"""
import os
from utils.Advertisement import Advertisement


class ObjectBuffer:

    def __init__(self, cv):
        self._buf = []
        self._cv = cv

    def _add_dir(self, dirpath):
        for item in self._buf:
            if item.dirpath == dirpath:
                return
        parent = os.path.dirname(dirpath.strip('/'))
        self._buf.append(Advertisement(parent, [dirpath], []))
        self._buf.append(Advertisement(dirpath, [], []))

    def _add_file(self, filename):
        dirpath = os.path.dirname(filename)
        for item in self._buf:
            if item.dirpath == dirpath:
                item.addFilename(filename)
                return
        adv = Advertisement(dirpath, [], [filename.lstrip(dirpath).lstrip('/')])
        self._buf.append(adv)

    def add(self, item, isFile=True):
        if item not in self._buf:
            self._cv.acquire()
            if isFile:
                self._add_file(item)
            else:
                self._add_dir(item)
            self._cv.notify()
            self._cv.release()

    def isEmpty(self):
        if self._buf:
            return False
        return True

    def getAllAdvertisements(self):
        return self._buf

    def clear(self):
        self._buf = []
