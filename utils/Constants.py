

def constant(f):
    def fset(self, value):
        raise TypeError
    def fget(self):
        return f()
    return property(fget, fset)

class _Response(object):
    @constant
    def OK():               return "OK"
    @constant
    def NO_EXIST():         return "NO_EXIST"
    @constant
    def EXISTS():           return "EXISTS"
    @constant
    def INVALID_COMMAND():  return "INVALID_COMMAND"
    @constant
    def CANT_LIST():        return "CANT_LIST"
    @constant
    def ERROR():            return "ERROR"

Response = _Response()