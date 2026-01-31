"""Example: List all tables in a database."""
from goosefs_metastore_client import GoosefsMetastoreClient

GOOSEFS_HOST = "localhost"
GOOSEFS_PORT = 9200
DATABASE_NAME = "my_database"

with GoosefsMetastoreClient(GOOSEFS_HOST, GOOSEFS_PORT) as client:
    tables = client.get_all_tables(DATABASE_NAME)
    
    print(f"Found {len(tables)} table(s) in database '{DATABASE_NAME}':")
    for tb_info in tables:
        print(f"  - Name: {tb_info.name}")
        print(f"    Is Mount: {tb_info.is_mount}")
        if tb_info.read_type:
            print(f"    Read Type: {tb_info.read_type}")
        if tb_info.write_type:
            print(f"    Write Type: {tb_info.write_type}")
        print()
