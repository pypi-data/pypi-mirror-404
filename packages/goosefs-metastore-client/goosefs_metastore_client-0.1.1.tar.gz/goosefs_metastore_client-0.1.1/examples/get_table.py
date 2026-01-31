"""Example: Get a specific table from GooseFS catalog."""
from goosefs_metastore_client import GoosefsMetastoreClient

GOOSEFS_HOST = "localhost"
GOOSEFS_PORT = 9200
DATABASE_NAME = "my_database"
TABLE_NAME = "my_table"

with GoosefsMetastoreClient(GOOSEFS_HOST, GOOSEFS_PORT) as client:
    table = client.get_table(DATABASE_NAME, TABLE_NAME)
    
    print(f"Table: {table.table_name}")
    print(f"Database: {table.db_name}")
    print(f"Owner: {table.owner}")
    print(f"Type: {table.type}")
    
    if table.schema and table.schema.cols:
        print("\nColumns:")
        for col in table.schema.cols:
            print(f"  - {col.name} ({col.type})")
            if col.comment:
                print(f"    Comment: {col.comment}")
    
    if table.partition_cols:
        print("\nPartition Columns:")
        for col in table.partition_cols:
            print(f"  - {col.name} ({col.type})")
    
    if table.parameters:
        print("\nParameters:")
        for key, value in table.parameters.items():
            print(f"  {key}: {value}")
