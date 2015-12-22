"""
Advertisement

Represents an update advertisement sent from a Node to the Directory Server notifying it about updates to its file
structure.
"""
import json


class Advertisement:

    def __init__(self, dirpath, dirnames, filenames):
        self.dirpath = dirpath
        self.dirnames = dirnames
        self.filenames = filenames

    def addDirname(self, dirname):
        if dirname not in self.dirnames:
            self.dirnames.append(dirname)

    def addFilename(self, filename):
        if filename not in self.filenames:
            self.filenames.append(filename)

    def toJSON(self):
        dict = {'dirpath': self.dirpath, 'dirnames': self.dirnames, 'filenames': self.filenames}
        return json.dumps(dict)
