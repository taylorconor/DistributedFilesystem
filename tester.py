import thread, socket, sys, time

def requester(host, port, message):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    # send the request using the socket
    s.send(message+"\n")
    # recieve up to 1024 bytes from the remote server
    data = s.recv(1024)
    print(data)
    s.close()

def send_file(host, port, filename, newfilename):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    s.send("PUT /"+newfilename)
    dat = s.recv(8096)
    print "Received: "+dat
    if dat != "OK":
        print "ERROR"
        return
    f = open(filename, "rb")
    l = f.read(1024)
    while (l):
        s.send(l)
        l = f.read(1024)
    f.close()
    s.shutdown(socket.SHUT_WR)
    s.close()

def get_file(host, port, filename, newfilename):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    s.send("GET /"+filename)
    f = open(newfilename, "wb")
    l = s.recv(1024)
    if l == "NO_EXIST" or l == "ERR":
        print l
        return
    while l:
        f.write(l)
        l = s.recv(1024)
    f.close()
