import sys, signal, time

def signal_handler(signal, frame):
    print "Shutting down..."
    sys.exit()

if len(sys.argv) <= 1:
    print "Usage: "

elif sys.argv[1] == "--masternode":
    print "Starting master node..."

elif sys.argv[1] == "--node":
    print "Starting ordinary node..."
    from node import Node
    dir = sys.argv[2]
    node = Node(dir)
    signal.signal(signal.SIGINT, signal_handler)
    while True:
        time.sleep(1)

elif sys.argv[1] == "--directory":
    print "Starting directory server..."