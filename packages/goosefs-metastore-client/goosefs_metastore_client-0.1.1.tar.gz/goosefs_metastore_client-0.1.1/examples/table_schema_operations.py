"""Example: Table schema operations.

This example demonstrates schema management:
- update_table_schema_metadata: Update schema (Lance metadata / GooseFS schema)
- alter_table_add_columns: Add columns
- alter_table_alter_columns: Modify columns
- alter_table_drop_columns: Drop columns
"""
from goosefs_metastore_client import GoosefsMetastoreClient
from grpc_files.table_master_pb2 import (
    UpdateTableSchemaMetadataPRequest,
    AlterTableAddColumnsPRequest,
    AlterTableAlterColumnsPRequest,
    AlterTableDropColumnsPRequest,
)

GOOSEFS_HOST = "localhost"
GOOSEFS_PORT = 9200


def example_update_schema_lance_style():
    """Update table schema using Lance style metadata field."""
    print("=" * 60)
    print("Example: Update Table Schema Metadata - Lance Style")
    print("=" * 60)
    
    with GoosefsMetastoreClient(GOOSEFS_HOST, GOOSEFS_PORT) as client:
        request = UpdateTableSchemaMetadataPRequest()
        request.id.extend(["my_catalog", "my_database", "my_table"])
        request.metadata = "col1 INT, col2 STRING, col3 DOUBLE"  # Lance field
        
        print(f"  Table ID: {list(request.id)}")
        print(f"  Metadata (Lance): {request.metadata}")
        
        try:
            client.update_table_schema_metadata(request)
            print(f"  Schema metadata updated successfully!")
        except Exception as e:
            print(f"  Update failed: {e}")


def example_update_schema_goosefs_style():
    """Update table schema using GooseFS style schema field."""
    print("=" * 60)
    print("Example: Update Table Schema Metadata - GooseFS Style")
    print("=" * 60)
    
    with GoosefsMetastoreClient(GOOSEFS_HOST, GOOSEFS_PORT) as client:
        request = UpdateTableSchemaMetadataPRequest()
        request.id.extend(["my_catalog", "my_database", "my_table"])
        request.schema = "col1 INT, col2 STRING, col3 DOUBLE"  # GooseFS field
        
        print(f"  Table ID: {list(request.id)}")
        print(f"  Schema (GooseFS): {request.schema}")
        
        try:
            client.update_table_schema_metadata(request)
            print(f"  Schema updated successfully!")
        except Exception as e:
            print(f"  Update failed: {e}")


def example_add_columns():
    """Add new columns to a table."""
    print("=" * 60)
    print("Example: Add Columns to Table")
    print("=" * 60)
    
    with GoosefsMetastoreClient(GOOSEFS_HOST, GOOSEFS_PORT) as client:
        request = AlterTableAddColumnsPRequest()
        request.id.extend(["my_catalog", "my_database", "my_table"])
        request.columns.extend([
            "new_col1 STRING",
            "new_col2 INT DEFAULT 0",
            "new_col3 TIMESTAMP"
        ])
        
        print(f"  Table ID: {list(request.id)}")
        print(f"  New columns:")
        for col in request.columns:
            print(f"    - {col}")
        
        try:
            client.alter_table_add_columns(request)
            print(f"  Columns added successfully!")
        except Exception as e:
            print(f"  Add columns failed: {e}")


def example_alter_columns():
    """Modify existing columns in a table."""
    print("=" * 60)
    print("Example: Alter Columns in Table")
    print("=" * 60)
    
    with GoosefsMetastoreClient(GOOSEFS_HOST, GOOSEFS_PORT) as client:
        request = AlterTableAlterColumnsPRequest()
        request.id.extend(["my_catalog", "my_database", "my_table"])
        request.columns.extend([
            "col1 BIGINT",  # Change INT to BIGINT
            "col2 VARCHAR(255)"  # Change STRING to VARCHAR
        ])
        
        print(f"  Table ID: {list(request.id)}")
        print(f"  Modified columns:")
        for col in request.columns:
            print(f"    - {col}")
        
        try:
            client.alter_table_alter_columns(request)
            print(f"  Columns altered successfully!")
        except Exception as e:
            print(f"  Alter columns failed: {e}")


def example_drop_columns():
    """Drop columns from a table."""
    print("=" * 60)
    print("Example: Drop Columns from Table")
    print("=" * 60)
    
    with GoosefsMetastoreClient(GOOSEFS_HOST, GOOSEFS_PORT) as client:
        request = AlterTableDropColumnsPRequest()
        request.id.extend(["my_catalog", "my_database", "my_table"])
        request.columns.extend(["old_col1", "deprecated_col"])
        
        print(f"  Table ID: {list(request.id)}")
        print(f"  Columns to drop: {list(request.columns)}")
        
        try:
            client.alter_table_drop_columns(request)
            print(f"  Columns dropped successfully!")
        except Exception as e:
            print(f"  Drop columns failed: {e}")


def main():
    """Run all schema examples."""
    print()
    print("#" * 60)
    print("# Table Schema Operations Examples")
    print("#" * 60)
    print()
    
    # Update schema (dual style)
    example_update_schema_lance_style()
    print()
    example_update_schema_goosefs_style()
    print()
    
    # Column operations
    example_add_columns()
    print()
    example_alter_columns()
    print()
    example_drop_columns()
    print()


if __name__ == "__main__":
    main()
