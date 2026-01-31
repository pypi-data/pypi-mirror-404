"""Example: Mount a table to GooseFS."""
from goosefs_metastore_client import GoosefsMetastoreClient

GOOSEFS_HOST = "localhost"
GOOSEFS_PORT = 9200
DATABASE_NAME = "my_database"
TABLE_NAME = "my_table"

with GoosefsMetastoreClient(GOOSEFS_HOST, GOOSEFS_PORT) as client:
    success = client.mount_table(DATABASE_NAME, TABLE_NAME)
    
    if success:
        print(f"Table '{DATABASE_NAME}.{TABLE_NAME}' mounted successfully!")
    else:
        print(f"Failed to mount table '{DATABASE_NAME}.{TABLE_NAME}'")
