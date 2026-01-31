"""Complete example showing database and table operations."""
from goosefs_metastore_client import GoosefsMetastoreClient
from goosefs_metastore_client.builders import DatabaseBuilder

GOOSEFS_HOST = "localhost"
GOOSEFS_PORT = 9200

database = DatabaseBuilder(
    db_name="example_database",
    description="Example database for demonstration",
    location="/user/hive/warehouse/example_database.db",
    owner_name="admin",
).build()

with GoosefsMetastoreClient(GOOSEFS_HOST, GOOSEFS_PORT) as goosefs_client:
    print("=" * 60)
    print("GooseFS Metastore Client - Complete Example")
    print("=" * 60)
    print()
    
    print("1. Listing all databases...")
    databases = goosefs_client.get_all_databases()
    print(f"   Found {len(databases)} database(s)")
    for db in databases:
        print(f"   - {db.name} (Type: {db.type})")
    print()
    
    print("2. Attaching a new database...")
    try:
        sync_status = goosefs_client.attach_database(
            udb_type="hive",
            udb_db_name="hive_source_db",
            db_name="goosefs_attached_db",
            configuration={
                "hive.metastore.uris": "thrift://hive-metastore:9083",
            },
            ignore_sync_errors=False,
            auto_mount=True,
        )
        print(f"   Database attached successfully!")
        print(f"   - Tables updated: {len(sync_status.tables_updated)}")
        print(f"   - Tables unchanged: {len(sync_status.tables_unchanged)}")
    except Exception as e:
        print(f"   Failed to attach database: {e}")
    print()
    
    print("3. Getting database details...")
    try:
        db = goosefs_client.get_database("goosefs_attached_db")
        print(f"   Database: {db.db_name}")
        print(f"   Location: {db.location}")
        print(f"   Owner: {db.owner_name}")
    except Exception as e:
        print(f"   Database not found: {e}")
    print()
    
    print("4. Listing tables in a database...")
    try:
        tables = goosefs_client.get_all_tables("goosefs_attached_db")
        print(f"   Found {len(tables)} table(s)")
        for tb in tables[:5]:
            print(f"   - {tb.name} (Mounted: {tb.is_mount})")
    except Exception as e:
        print(f"   Failed to list tables: {e}")
    print()
    
    print("5. Mounting a table...")
    try:
        success = goosefs_client.mount_table("goosefs_attached_db", "sample_table")
        if success:
            print(f"   Table mounted successfully!")
        else:
            print(f"   Failed to mount table")
    except Exception as e:
        print(f"   Error mounting table: {e}")
    print()
    
    print("6. Getting table details...")
    try:
        table_info = goosefs_client.get_table("goosefs_attached_db", "sample_table")
        print(f"   Table: {table_info.table_name}")
        print(f"   Database: {table_info.db_name}")
        print(f"   Owner: {table_info.owner}")
        
        if table_info.schema and table_info.schema.cols:
            print(f"   Columns ({len(table_info.schema.cols)}):")
            for col in table_info.schema.cols[:5]:
                print(f"     - {col.name}: {col.type}")
        
        if table_info.partition_cols:
            print(f"   Partition Columns:")
            for col in table_info.partition_cols:
                print(f"     - {col.name}: {col.type}")
    except Exception as e:
        print(f"   Failed to get table: {e}")
    print()
    
    print("7. Getting access statistics...")
    try:
        stats = goosefs_client.access_stat(days=7, top_nums=5)
        print(f"   Top {len(stats)} accessed tables:")
        for i, stat in enumerate(stats, 1):
            print(f"     {i}. {stat.db_name}.{stat.tb_name} ({stat.hots} accesses)")
    except Exception as e:
        print(f"   Failed to get statistics: {e}")
    print()
    
    print("8. Syncing database...")
    try:
        sync_status = goosefs_client.sync_database("goosefs_attached_db")
        print(f"   Database synced!")
        print(f"   - Tables updated: {len(sync_status.tables_updated)}")
        print(f"   - Tables unchanged: {len(sync_status.tables_unchanged)}")
    except Exception as e:
        print(f"   Failed to sync database: {e}")
    print()
    
    print("=" * 60)
    print("Example completed!")
    print("=" * 60)
