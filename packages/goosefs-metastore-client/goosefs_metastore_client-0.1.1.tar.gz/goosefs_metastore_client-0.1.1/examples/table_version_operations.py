"""Example: Table version and restore operations.

This example demonstrates version management:
- list_table_versions: List table versions
- restore_table: Restore table to a specific version
- rename_table: Rename a table
- list_all_tables: List all tables with pagination
- list_tables: List tables in namespace
"""
from goosefs_metastore_client import GoosefsMetastoreClient
from grpc_files.table_master_pb2 import (
    ListTableVersionsPRequest,
    RestoreTablePRequest,
    RenameTablePRequest,
    ListAllTablesPRequest,
    ListTablesPRequest,
)

GOOSEFS_HOST = "localhost"
GOOSEFS_PORT = 9200


def example_list_table_versions():
    """List all versions of a table."""
    print("=" * 60)
    print("Example: List Table Versions")
    print("=" * 60)
    
    with GoosefsMetastoreClient(GOOSEFS_HOST, GOOSEFS_PORT) as client:
        request = ListTableVersionsPRequest()
        request.id.extend(["my_catalog", "my_database", "my_table"])
        
        try:
            versions = client.list_table_versions(request)
            print(f"Table has {len(versions)} version(s):")
            for v in versions:
                print(f"  - Version {v}")
        except Exception as e:
            print(f"Failed to list versions: {e}")


def example_restore_table():
    """Restore a table to a specific version."""
    print("=" * 60)
    print("Example: Restore Table")
    print("=" * 60)
    
    with GoosefsMetastoreClient(GOOSEFS_HOST, GOOSEFS_PORT) as client:
        request = RestoreTablePRequest()
        request.id.extend(["my_catalog", "my_database", "my_table"])
        request.version = 5  # Version to restore to
        
        print(f"  Restoring table to version {request.version}...")
        
        try:
            client.restore_table(request)
            print(f"  Table restored successfully!")
        except Exception as e:
            print(f"  Restore failed: {e}")


def example_rename_table():
    """Rename a table."""
    print("=" * 60)
    print("Example: Rename Table")
    print("=" * 60)
    
    with GoosefsMetastoreClient(GOOSEFS_HOST, GOOSEFS_PORT) as client:
        request = RenameTablePRequest()
        request.old_id.extend(["my_catalog", "my_database", "old_table_name"])
        request.new_id.extend(["my_catalog", "my_database", "new_table_name"])
        
        print(f"  Old name: {list(request.old_id)}")
        print(f"  New name: {list(request.new_id)}")
        
        try:
            client.rename_table(request)
            print(f"  Table renamed successfully!")
        except Exception as e:
            print(f"  Rename failed: {e}")


def example_list_tables_in_namespace():
    """List tables in a specific namespace."""
    print("=" * 60)
    print("Example: List Tables in Namespace")
    print("=" * 60)
    
    with GoosefsMetastoreClient(GOOSEFS_HOST, GOOSEFS_PORT) as client:
        request = ListTablesPRequest()
        request.id.extend(["my_catalog", "my_database"])
        request.page_token = ""
        request.limit = 20
        
        try:
            result = client.list_tables(request)
            tables = result.get("tables", [])
            print(f"Found {len(tables)} table(s):")
            for tb in tables:
                print(f"  - {tb}")
            
            if "page_token" in result and result["page_token"]:
                print(f"\nNext page token: {result['page_token']}")
        except Exception as e:
            print(f"Failed to list tables: {e}")


def example_list_all_tables():
    """List all tables across namespaces."""
    print("=" * 60)
    print("Example: List All Tables")
    print("=" * 60)
    
    with GoosefsMetastoreClient(GOOSEFS_HOST, GOOSEFS_PORT) as client:
        request = ListAllTablesPRequest()
        request.page_token = ""
        request.limit = 50
        
        try:
            result = client.list_all_tables(request)
            tables = result.get("tables", [])
            print(f"Found {len(tables)} table(s) across all namespaces:")
            for tb in tables[:10]:  # Show first 10
                print(f"  - {tb}")
            
            if len(tables) > 10:
                print(f"  ... and {len(tables) - 10} more")
            
            if "page_token" in result and result["page_token"]:
                print(f"\nNext page token: {result['page_token']}")
        except Exception as e:
            print(f"Failed to list all tables: {e}")


def main():
    """Run all version and management examples."""
    print()
    print("#" * 60)
    print("# Table Version & Management Operations Examples")
    print("#" * 60)
    print()
    
    example_list_table_versions()
    print()
    example_restore_table()
    print()
    example_rename_table()
    print()
    example_list_tables_in_namespace()
    print()
    example_list_all_tables()
    print()


if __name__ == "__main__":
    main()
