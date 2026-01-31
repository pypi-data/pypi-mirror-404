"""Example: Attach a database to GooseFS catalog."""
from goosefs_metastore_client import GoosefsMetastoreClient

GOOSEFS_HOST = "localhost"
GOOSEFS_PORT = 9200

with GoosefsMetastoreClient(GOOSEFS_HOST, GOOSEFS_PORT) as client:
    sync_status = client.attach_database(
        udb_type="hive",
        udb_db_name="source_database",
        db_name="goosefs_database",
        configuration={
            "hive.metastore.uris": "thrift://hive-metastore:9083",
        },
        ignore_sync_errors=False,
        auto_mount=True,
    )
    
    print("Database attached successfully!")
    print(f"Tables updated: {len(sync_status.tables_updated)}")
    print(f"Tables unchanged: {len(sync_status.tables_unchanged)}")
    print(f"Tables removed: {len(sync_status.tables_removed)}")
    print(f"Tables ignored: {len(sync_status.tables_ignored)}")
    
    if sync_status.tables_errors:
        print("Errors:")
        for table, error in sync_status.tables_errors.items():
            print(f"  {table}: {error}")
