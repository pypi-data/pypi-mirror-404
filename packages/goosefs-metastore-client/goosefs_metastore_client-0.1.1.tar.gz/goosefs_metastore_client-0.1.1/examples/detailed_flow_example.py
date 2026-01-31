"""
Detailed example showing the complete call flow as described in the user's diagram.

This example demonstrates:
1. Creating database object using builder
2. Using GoosefsMetastoreClient (Python equivalent of TableShell)
3. Calling listDatabases which internally:
   - Calls RetryHandlingTableMasterClient (implemented in GoosefsMetastoreClient)
   - Sends gRPC request to TABLE_MASTER_CLIENT_SERVICE
   - GooseFSMaster receives and processes the request
   - TableMasterClientServiceHandler routes to DefaultTableMaster
   - Response flows back through all layers
"""

from goosefs_metastore_client import GoosefsMetastoreClient
from goosefs_metastore_client.builders import DatabaseBuilder

GOOSEFS_HOST = "localhost"
GOOSEFS_PORT = 9200


def main():
    print("=" * 80)
    print("GooseFS Metastore Client - Detailed Call Flow Example")
    print("=" * 80)
    print()
    
    print("Step 1: Creating database object using builder")
    print("-" * 80)
    database = DatabaseBuilder(
        db_name="example_database",
        description="Example database created with builder",
        location="/user/hive/warehouse/example_database.db",
        owner_name="admin",
        parameters={
            "created_by": "python_client",
            "version": "1.0",
        },
    ).build()
    print(f"✓ Database object created: {database.db_name}")
    print(f"  - Location: {database.location}")
    print(f"  - Owner: {database.owner_name}")
    print()
    
    print("Step 2: Creating GoosefsMetastoreClient (Python Client Side)")
    print("-" * 80)
    print(f"  Connecting to GooseFS Master at {GOOSEFS_HOST}:{GOOSEFS_PORT}")
    print("  This is equivalent to creating TableMasterClient in Java")
    print()
    
    try:
        with GoosefsMetastoreClient(GOOSEFS_HOST, GOOSEFS_PORT) as goosefs_client:
            print("✓ Connection established to GooseFS Table Master")
            print()
            
            print("Step 3: Calling get_all_databases()")
            print("-" * 80)
            print("  Python Call Chain:")
            print("    goosefs_client.get_all_databases()")
            print("      → GoosefsMetastoreClient._call_with_retry()")
            print("      → TableMasterClientServiceStub.GetAllDatabases()")
            print("      → [gRPC Network Call to GooseFS Master]")
            print()
            print("  Java Server Call Chain:")
            print("    GooseFSMaster Process receives gRPC request")
            print("      → TableMasterClientServiceHandler.getAllDatabases()")
            print("      → DefaultTableMaster.getAllDatabases()")
            print("      → Returns List<DbInfo>")
            print("      → Response flows back through gRPC")
            print()
            
            databases = goosefs_client.get_all_databases()
            
            print(f"✓ Received response with {len(databases)} database(s)")
            print()
            
            if databases:
                print("Database List:")
                for i, db_info in enumerate(databases, 1):
                    print(f"  {i}. {db_info.name}")
                    print(f"     Type: {db_info.type}")
                    print(f"     Auto Mount: {db_info.auto_mount}")
                    if db_info.default_write_type:
                        print(f"     Default Write Type: {db_info.default_write_type}")
                    print()
            else:
                print("  No databases found in catalog")
                print()
            
            print("Step 4: Getting detailed database information")
            print("-" * 80)
            if databases:
                db_name = databases[0].name
                print(f"  Getting details for database: {db_name}")
                print()
                
                try:
                    db_detail = goosefs_client.get_database(db_name)
                    print(f"✓ Database Details:")
                    print(f"  - Name: {db_detail.db_name}")
                    print(f"  - Description: {db_detail.description}")
                    print(f"  - Location: {db_detail.location}")
                    print(f"  - Owner: {db_detail.owner_name}")
                    
                    if db_detail.parameter:
                        print(f"  - Parameters:")
                        for key, value in db_detail.parameter.items():
                            print(f"      {key}: {value}")
                    print()
                except Exception as e:
                    print(f"✗ Failed to get database details: {e}")
                    print()
                
                print("Step 5: Listing tables in database")
                print("-" * 80)
                try:
                    tables = goosefs_client.get_all_tables(db_name)
                    print(f"✓ Found {len(tables)} table(s) in database '{db_name}'")
                    
                    for i, table in enumerate(tables[:5], 1):
                        print(f"  {i}. {table.name}")
                        print(f"     Is Mounted: {table.is_mount}")
                        if table.read_type:
                            print(f"     Read Type: {table.read_type}")
                        if table.write_type:
                            print(f"     Write Type: {table.write_type}")
                    
                    if len(tables) > 5:
                        print(f"  ... and {len(tables) - 5} more tables")
                    print()
                except Exception as e:
                    print(f"✗ Failed to list tables: {e}")
                    print()
    
    except Exception as e:
        print(f"\n✗ Connection Error: {e}")
        print()
        print("Note: Make sure GooseFS master is running with Table Master service enabled.")
        print("      The Table Master client service should be accessible on port 9200.")
        print()
    
    print("=" * 80)
    print("Call Flow Demonstration Complete")
    print("=" * 80)
    print()
    print("Summary of Call Flow:")
    print("  1. User creates database/table objects with Builders")
    print("  2. User calls methods on GoosefsMetastoreClient")
    print("  3. GoosefsMetastoreClient creates gRPC request messages")
    print("  4. GoosefsMetastoreClient calls gRPC stub with retry logic")
    print("  5. gRPC stub serializes request and sends over network")
    print("  6. GooseFS Master receives request")
    print("  7. TableMasterClientServiceHandler processes request")
    print("  8. DefaultTableMaster executes business logic")
    print("  9. Response flows back through all layers")
    print(" 10. User receives typed Python objects (DbInfo, TableInfo, etc.)")


if __name__ == "__main__":
    main()
