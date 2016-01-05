import sys, signal, time

if __name__ == "__main__":
    def signal_handler(signal, frame):
        print "Shutting down..."
        sys.exit()

    if len(sys.argv) <= 1:
        print "No mode specified!"

    elif sys.argv[1] == "--node":
        if len(sys.argv) != 9:
            print "Usage: python " + sys.argv[0] + " --node [dir] [host] [port] [ds_host] [ds_port] [rm_host] [rm_port]"
            sys.exit()
        print "Starting node..."
        from Node import Node
        dir = sys.argv[2]
        host = sys.argv[3]
        port = int(sys.argv[4])
        ds_host = sys.argv[5]
        ds_port = int(sys.argv[6])
        rm_host = sys.argv[7]
        rm_port = int(sys.argv[8])
        node = Node(dir, host, port, ds_host, ds_port, rm_host, rm_port)
        print "Node started successfully."

    elif sys.argv[1] == "--directory":
        if len(sys.argv) != 3:
            print "Usage: python " + sys.argv[0] + " --directory [port]"
            sys.exit()
        print "Starting Directory Server..."
        from DirectoryServer import DirectoryServer
        port = int(sys.argv[2])
        ds = DirectoryServer(port)
        print "Directory Server started successfully."

    elif sys.argv[1] == "--replication":
        if len(sys.argv) != 3:
            print "Usage: python " + sys.argv[0] + " --replication [port]"
            sys.exit()
        print "Starting replication manager..."
        from ReplicationManager import ReplicationManager
        port = int(sys.argv[2])
        rm = ReplicationManager(port)
        print "Replication Manager started successfully."

    signal.signal(signal.SIGINT, signal_handler)
    while True:
        time.sleep(1)