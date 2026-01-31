"""Example: List all databases from GooseFS catalog."""
from goosefs_metastore_client import GoosefsMetastoreClient

GOOSEFS_HOST = "localhost"
GOOSEFS_PORT = 9200

with GoosefsMetastoreClient(GOOSEFS_HOST, GOOSEFS_PORT) as client:
    databases = client.get_all_databases()
    
    print(f"Found {len(databases)} database(s):")
    for db_info in databases:
        print(f"  - Name: {db_info.name}")
        print(f"    Type: {db_info.type}")
        print(f"    Auto Mount: {db_info.auto_mount}")
        if db_info.default_write_type:
            print(f"    Default Write Type: {db_info.default_write_type}")
        if db_info.default_read_type:
            print(f"    Default Read Type: {db_info.default_read_type}")
        print()
