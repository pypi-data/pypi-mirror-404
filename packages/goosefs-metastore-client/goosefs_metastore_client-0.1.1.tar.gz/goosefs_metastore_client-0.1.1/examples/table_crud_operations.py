"""Example: Table CRUD operations with Lance/GooseFS compatible styles.

This example demonstrates table creation, reading, updating, and deletion:
- create_table: Create a table with schema
- create_empty_table: Create an empty table
- insert_into_table: Insert data into table
- merge_insert_into_table: Merge insert data
- update_table: Update table records (Lance predicate / GooseFS where_clause)
- delete_from_table: Delete records (Lance predicate / GooseFS where_clause)
- query_table: Query table data
- count_table_rows: Count rows (with optional Lance predicate and version)
"""
from goosefs_metastore_client import GoosefsMetastoreClient
from grpc_files.table_master_pb2 import (
    CreateTablePRequest,
    CreateEmptyTablePRequest,
    InsertIntoTablePRequest,
    MergeInsertIntoTablePRequest,
    UpdateTablePRequest,
    DeleteFromTablePRequest,
    QueryTablePRequest,
    CountTableRowsPRequest,
    DropTablePRequest,
    TableExistsPRequest,
    DescribeTablePRequest,
    RegisterTablePRequest,
    DeregisterTablePRequest,
)

GOOSEFS_HOST = "localhost"
GOOSEFS_PORT = 9200


def example_create_table():
    """Create a new table with schema and properties."""
    print("=" * 60)
    print("Example: Create Table")
    print("=" * 60)
    
    with GoosefsMetastoreClient(GOOSEFS_HOST, GOOSEFS_PORT) as client:
        request = CreateTablePRequest()
        request.id.extend(["my_catalog", "my_database", "new_table"])
        request.schema = "id INT, name STRING, age INT, created_at TIMESTAMP"
        request.location = "s3://my-bucket/tables/new_table"
        request.mode = "CREATE"  # CREATE, CREATE_IF_NOT_EXISTS
        request.properties["format"] = "lance"
        request.properties["compression"] = "zstd"
        
        try:
            result = client.create_table(request)
            print(f"Table created successfully!")
            print(f"  Location: {result.get('location', 'N/A')}")
            print(f"  Storage Options: {result.get('storage_options', {})}")
        except Exception as e:
            print(f"Failed to create table: {e}")


def example_create_empty_table():
    """Create an empty table."""
    print("=" * 60)
    print("Example: Create Empty Table")
    print("=" * 60)
    
    with GoosefsMetastoreClient(GOOSEFS_HOST, GOOSEFS_PORT) as client:
        request = CreateEmptyTablePRequest()
        request.id.extend(["my_catalog", "my_database", "empty_table"])
        request.schema = "id INT, value DOUBLE"
        request.location = "s3://my-bucket/tables/empty_table"
        request.mode = "CREATE"
        
        try:
            result = client.create_empty_table(request)
            print(f"Empty table created!")
            print(f"  Location: {result.get('location', 'N/A')}")
        except Exception as e:
            print(f"Failed to create empty table: {e}")


def example_insert_into_table():
    """Insert data into a table."""
    print("=" * 60)
    print("Example: Insert Into Table")
    print("=" * 60)
    
    with GoosefsMetastoreClient(GOOSEFS_HOST, GOOSEFS_PORT) as client:
        request = InsertIntoTablePRequest()
        request.id.extend(["my_catalog", "my_database", "my_table"])
        request.data = "[(1, 'Alice', 25), (2, 'Bob', 30)]"
        request.mode = "APPEND"  # APPEND, OVERWRITE
        
        try:
            rows_affected = client.insert_into_table(request)
            print(f"Inserted {rows_affected} row(s)")
        except Exception as e:
            print(f"Failed to insert data: {e}")


def example_merge_insert():
    """Merge insert data into a table (upsert operation)."""
    print("=" * 60)
    print("Example: Merge Insert Into Table")
    print("=" * 60)
    
    with GoosefsMetastoreClient(GOOSEFS_HOST, GOOSEFS_PORT) as client:
        request = MergeInsertIntoTablePRequest()
        request.id.extend(["my_catalog", "my_database", "my_table"])
        request.data = "[(1, 'Alice Updated', 26), (3, 'Charlie', 35)]"
        request.on_columns.extend(["id"])  # Columns to match on
        
        try:
            rows_affected = client.merge_insert_into_table(request)
            print(f"Merge affected {rows_affected} row(s)")
        except Exception as e:
            print(f"Failed to merge insert: {e}")


def example_update_table_lance_style():
    """Update table using Lance style predicate field."""
    print("=" * 60)
    print("Example: Update Table - Lance Style")
    print("=" * 60)
    
    with GoosefsMetastoreClient(GOOSEFS_HOST, GOOSEFS_PORT) as client:
        request = UpdateTablePRequest()
        request.id.extend(["my_catalog", "my_database", "my_table"])
        request.updates = "status = 'inactive', updated_at = NOW()"
        request.predicate = "last_login < '2024-01-01'"  # Lance field
        
        print(f"  Table ID: {list(request.id)}")
        print(f"  Updates: {request.updates}")
        print(f"  Predicate (Lance): {request.predicate}")
        
        try:
            rows_affected = client.update_table(request)
            print(f"  Updated {rows_affected} row(s)")
        except Exception as e:
            print(f"  Update failed: {e}")


def example_update_table_goosefs_style():
    """Update table using GooseFS style where_clause field."""
    print("=" * 60)
    print("Example: Update Table - GooseFS Style")
    print("=" * 60)
    
    with GoosefsMetastoreClient(GOOSEFS_HOST, GOOSEFS_PORT) as client:
        request = UpdateTablePRequest()
        request.id.extend(["my_catalog", "my_database", "my_table"])
        request.updates = "age = age + 1"
        request.where_clause = "birthday = CURRENT_DATE()"  # GooseFS field
        
        print(f"  Table ID: {list(request.id)}")
        print(f"  Updates: {request.updates}")
        print(f"  Where Clause (GooseFS): {request.where_clause}")
        
        try:
            rows_affected = client.update_table(request)
            print(f"  Updated {rows_affected} row(s)")
        except Exception as e:
            print(f"  Update failed: {e}")


def example_delete_from_table_lance_style():
    """Delete from table using Lance style predicate field."""
    print("=" * 60)
    print("Example: Delete From Table - Lance Style")
    print("=" * 60)
    
    with GoosefsMetastoreClient(GOOSEFS_HOST, GOOSEFS_PORT) as client:
        request = DeleteFromTablePRequest()
        request.id.extend(["my_catalog", "my_database", "my_table"])
        request.predicate = "age > 18 AND status = 'active'"  # Lance field
        
        print(f"  Table ID: {list(request.id)}")
        print(f"  Predicate (Lance): {request.predicate}")
        
        try:
            rows_affected = client.delete_from_table(request)
            print(f"  Deleted {rows_affected} row(s)")
        except Exception as e:
            print(f"  Delete failed: {e}")


def example_delete_from_table_goosefs_style():
    """Delete from table using GooseFS style where_clause field."""
    print("=" * 60)
    print("Example: Delete From Table - GooseFS Style")
    print("=" * 60)
    
    with GoosefsMetastoreClient(GOOSEFS_HOST, GOOSEFS_PORT) as client:
        request = DeleteFromTablePRequest()
        request.id.extend(["my_catalog", "my_database", "my_table"])
        request.where_clause = "age > 18 AND status = 'active'"  # GooseFS field
        
        print(f"  Table ID: {list(request.id)}")
        print(f"  Where Clause (GooseFS): {request.where_clause}")
        
        try:
            rows_affected = client.delete_from_table(request)
            print(f"  Deleted {rows_affected} row(s)")
        except Exception as e:
            print(f"  Delete failed: {e}")


def example_query_table():
    """Query data from a table."""
    print("=" * 60)
    print("Example: Query Table")
    print("=" * 60)
    
    with GoosefsMetastoreClient(GOOSEFS_HOST, GOOSEFS_PORT) as client:
        request = QueryTablePRequest()
        request.id.extend(["my_catalog", "my_database", "my_table"])
        request.query = "SELECT * FROM table WHERE age > 20"
        request.limit = 100
        
        try:
            result = client.query_table(request)
            print(f"Query result: {result}")
        except Exception as e:
            print(f"Query failed: {e}")


def example_count_rows_basic():
    """Count rows in a table."""
    print("=" * 60)
    print("Example: Count Table Rows (Basic)")
    print("=" * 60)
    
    with GoosefsMetastoreClient(GOOSEFS_HOST, GOOSEFS_PORT) as client:
        request = CountTableRowsPRequest()
        request.id.extend(["my_catalog", "my_database", "my_table"])
        
        try:
            count = client.count_table_rows(request)
            print(f"Total rows: {count}")
        except Exception as e:
            print(f"Count failed: {e}")


def example_count_rows_with_filter():
    """Count rows with predicate filter (Lance compatible)."""
    print("=" * 60)
    print("Example: Count Table Rows (With Filter - Lance Style)")
    print("=" * 60)
    
    with GoosefsMetastoreClient(GOOSEFS_HOST, GOOSEFS_PORT) as client:
        request = CountTableRowsPRequest()
        request.id.extend(["my_catalog", "my_database", "my_table"])
        request.predicate = "status = 'active'"  # Lance field
        request.version = 10  # Lance field - specific table version
        
        print(f"  Table ID: {list(request.id)}")
        print(f"  Predicate: {request.predicate}")
        print(f"  Version: {request.version}")
        
        try:
            count = client.count_table_rows(request)
            print(f"  Filtered rows: {count}")
        except Exception as e:
            print(f"  Count failed: {e}")


def example_table_exists():
    """Check if a table exists."""
    print("=" * 60)
    print("Example: Table Exists")
    print("=" * 60)
    
    with GoosefsMetastoreClient(GOOSEFS_HOST, GOOSEFS_PORT) as client:
        request = TableExistsPRequest()
        request.id.extend(["my_catalog", "my_database", "my_table"])
        
        exists = client.table_exists(request)
        print(f"Table exists: {exists}")


def example_describe_table():
    """Describe a table to get its details."""
    print("=" * 60)
    print("Example: Describe Table")
    print("=" * 60)
    
    with GoosefsMetastoreClient(GOOSEFS_HOST, GOOSEFS_PORT) as client:
        request = DescribeTablePRequest()
        request.id.extend(["my_catalog", "my_database", "my_table"])
        request.version = 0  # 0 for latest version
        request.load_detailed_metadata = True
        
        try:
            result = client.describe_table(request)
            print(f"Table description:")
            print(f"  Location: {result.get('location', 'N/A')}")
            print(f"  Storage Options: {result.get('storage_options', {})}")
        except Exception as e:
            print(f"Describe failed: {e}")


def example_drop_table():
    """Drop a table."""
    print("=" * 60)
    print("Example: Drop Table")
    print("=" * 60)
    
    with GoosefsMetastoreClient(GOOSEFS_HOST, GOOSEFS_PORT) as client:
        request = DropTablePRequest()
        request.id.extend(["my_catalog", "my_database", "table_to_drop"])
        request.mode = "DROP"  # DROP, DROP_IF_EXISTS
        
        try:
            client.drop_table(request)
            print(f"Table dropped successfully!")
        except Exception as e:
            print(f"Drop failed: {e}")


def main():
    """Run all table CRUD examples."""
    print()
    print("#" * 60)
    print("# Table CRUD Operations Examples")
    print("#" * 60)
    print()
    
    # Create operations
    example_create_table()
    print()
    example_create_empty_table()
    print()
    
    # Table info operations
    example_table_exists()
    print()
    example_describe_table()
    print()
    
    # Data operations
    example_insert_into_table()
    print()
    example_merge_insert()
    print()
    example_query_table()
    print()
    
    # Count operations
    example_count_rows_basic()
    print()
    example_count_rows_with_filter()
    print()
    
    # Update operations (Lance vs GooseFS style)
    example_update_table_lance_style()
    print()
    example_update_table_goosefs_style()
    print()
    
    # Delete operations (Lance vs GooseFS style)
    example_delete_from_table_lance_style()
    print()
    example_delete_from_table_goosefs_style()
    print()
    
    # Drop operation
    example_drop_table()
    print()


if __name__ == "__main__":
    main()
