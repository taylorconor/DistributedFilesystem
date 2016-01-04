"""
ReplicationSet

"""

from utils.Constants import Replication

class ReplicationSet:

    def __init__(self):
        self._members = []

    def is_full(self):
        if self._members == Replication.SET_SIZE:
            return True
        return False

    def size(self):
        return len(self._members)

    def add(self, location):
        if self.is_full():
            return False
        self._members.append(location)
        return True

    def remove(self):
        if self.size() == 0:
            return None
        return self._members.pop()

    def contains(self, location):
        for item in self._members:
            if item.compare(location):
                return True
        return False

    def members(self):
        return self._members


class ReplicationController:

    def __init__(self):
        self._members = [ReplicationSet()]

    def add(self, location):
        # check if the previous replication set now needs to be broken down into two different (equally sized) sets
        if self._members[-1].size == Replication.SET_SIZE-1:
            new_set = ReplicationSet()
            new_set.add(location)
            for i in range(0, (Replication.SET_SIZE/2)-1):
                new_location = self._members[-1].remove()
                if new_location is not None:
                    new_set.add(new_location)
            self._members.append(new_set)
        # otherwise, we can just add the host to the last replication set. the last replication set will always have
        # a size of *at least* SET_SIZE, and *at most* (SET_SIZE*2)-1. this is to account for scenarios where the
        # amount of hosts in the system is not divisible evenly by SET_SIZE
        else:
            self._members[-1].add(location)

    def lookup(self, tuple):
        for member in self._members:
            if member.contains(tuple):
                return member.members()
        return None
