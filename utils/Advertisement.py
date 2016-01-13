"""
Advertisement

Represents an update advertisement sent from a Node to the Directory Server notifying it about updates to its file
structure.
"""
import json


class Advertisement:

    def __init__(self, dirpath, dirnames, filenames, deletelist=[]):
        self.dirpath = dirpath
        self.dirnames = dirnames
        self.filenames = filenames
        self.deletelist = deletelist

    def add_dirname(self, dirname):
        if dirname not in self.dirnames:
            self.dirnames.append(dirname)

    def add_filename(self, filename):
        if filename not in self.filenames:
            self.filenames.append(filename)

    def add_delete(self, item):
        if item.beginswith(self.dirpath):
            item = item[len(self.dirpath):].strip('/')
        if item not in self.deletelist:
            self.deletelist.append(item)

    def to_json(self):
        dict = {'dirpath': self.dirpath, 'dirnames': self.dirnames,
                'filenames': self.filenames, 'deletelist': self.deletelist}
        return json.dumps(dict)
