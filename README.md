#Distributed Filesystem
This filesystem operates using an upload/download model. It's components are: a distributed filesystem, a directory
service, replication, and a lock service.

##Components:
- **Node**: An ordinary fileserver node
  - Stores files in a directory hierarchy matching that of the entire filesystem, even if the node only stores files in one sub-directory
  - Advertises its contents to the Directory Server on startup
  - Advertises its identity to the Replication Manager on startup
- **DirectoryServer**: Directory Server node
  - Authoritative source on the hierarchy of the filesystem and the location of each file
  - Sends information about the contents of the filesystem and the location of files to clients that request it
  - Doesn't actually store or transfer files, just metadata
- **ReplicationManager**: Replication Manager server
  - Assigns each Node to a replication set
  - Responds to queries from nodes requesting the identity of other nodes in their set
- **LockServer**: Locking server
  - Provides a means for clients to guarantee unique access to a file or folder in the filesystem

##Usage:
A sample client usage of the filesystem:

1. Client contacts the Directory Server to list all files in the `/` directory.
2. The client decides to modify `/thesis.txt`, so he requests the location of that file from the Directory Server.
  * The Directory Server will reply with just *one* of the locations of the file. Due to replication, the file may be located on multiple servers.
3. Client contacts the Lock Server to lock `/thesis.txt` so he can download it without any other clients being able to edit it.
  * If the client cannot immediately obtain the lock, it must wait until the lock becomes free.
4. The client then contacts the node location received in step 2 and downloads the file.
5. The client modifies the file as needed.
6. The client contact the Directory Server again to find the location of `/thesis.txt`.
  * This is necessary because the node that the client downloaded the file from in step 4 may now have left the network, or may be part of a different replication set.
7. Client uploads the modified file to the location it received from step 6.
8. The client contacts the Lock Server again to unlock `/thesis.txt`.