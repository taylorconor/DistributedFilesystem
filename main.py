import sys, signal, time

if __name__ == "__main__":
    def signal_handler(signal, frame):
        print "Shutting down..."
        sys.exit()

    if len(sys.argv) <= 1:
        print "Usage: "

    elif sys.argv[1] == "--masternode":
        print "Starting master node..."

    elif sys.argv[1] == "--node":
        print "Starting ordinary node..."
        from Node import Node
        dir = sys.argv[2]
        host = sys.argv[3]
        port = int(sys.argv[4])
        ds_host = sys.argv[5]
        ds_port = int(sys.argv[6])
        node = Node(dir, host, port, ds_host, ds_port)

    elif sys.argv[1] == "--directory":
        print "Starting directory server..."
        from DirectoryServer import DirectoryServer
        port = int(sys.argv[2])
        ds = DirectoryServer(port)

    signal.signal(signal.SIGINT, signal_handler)
    while True:
        time.sleep(1)