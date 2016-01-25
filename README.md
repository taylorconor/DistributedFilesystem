#Distributed Filesystem
This filesystem operates using an upload/download model. It's components are: a distributed filesystem, a directory
service, replication.

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