

def constant(f):
    def fset(self, value):
        raise TypeError
    def fget(self):
        return f()
    return property(fget, fset)

class _Response(object):
    @constant
    def OK():               return "OK"                 # Acknowledgement
    @constant
    def NO_EXIST():         return "NO_EXIST"           # Item does not exist (e.g. get)
    @constant
    def EXISTS():           return "EXISTS"             # Item already exists (e.g. mkdir)
    @constant
    def IS_DIRECTORY():     return "IS_DIRECTORY"       # Item is directory (e.g. get)
    @constant
    def INVALID_COMMAND():  return "INVALID_COMMAND"    # Server cannot handle requested command
    @constant
    def CANT_LIST():        return "CANT_LIST"          # Server can't list (e.g. calling LIST on a file)
    @constant
    def ERROR():            return "ERROR"              # Server encountered an error, request not completed

class _Interval(object):
    @constant
    def ADVERTISE():        return 1                    # Propagate Advertise incremental updates every second

class _Replication(object):
    @constant
    def SET_SIZE():         return 3                    # 3 nodes per replication set

Response = _Response()
Interval = _Interval()
Replication = _Replication()