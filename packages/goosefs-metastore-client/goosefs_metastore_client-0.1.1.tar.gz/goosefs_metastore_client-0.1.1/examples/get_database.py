"""Example: Get a specific database from GooseFS catalog."""
from goosefs_metastore_client import GoosefsMetastoreClient

GOOSEFS_HOST = "localhost"
GOOSEFS_PORT = 9200
DATABASE_NAME = "my_database"

with GoosefsMetastoreClient(GOOSEFS_HOST, GOOSEFS_PORT) as client:
    database = client.get_database(DATABASE_NAME)
    
    print(f"Database: {database.db_name}")
    print(f"Description: {database.description}")
    print(f"Location: {database.location}")
    print(f"Owner: {database.owner_name}")
    print(f"Owner Type: {database.owner_type}")
    
    if database.parameter:
        print("Parameters:")
        for key, value in database.parameter.items():
            print(f"  {key}: {value}")
