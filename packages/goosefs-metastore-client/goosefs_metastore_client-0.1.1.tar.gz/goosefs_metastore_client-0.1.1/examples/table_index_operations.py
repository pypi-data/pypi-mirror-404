"""Example: Table index operations.

This example demonstrates table index management:
- create_table_index: Create vector/full-text index
- create_table_scalar_index: Create scalar index
- list_table_indices: List indices (with Lance pagination support)
- describe_table_index_stats: Get index statistics
- drop_table_index: Drop an index
"""
from goosefs_metastore_client import GoosefsMetastoreClient
from grpc_files.table_master_pb2 import (
    CreateTableIndexPRequest,
    CreateTableScalarIndexPRequest,
    ListTableIndicesPRequest,
    DescribeTableIndexStatsPRequest,
    DropTableIndexPRequest,
)

GOOSEFS_HOST = "localhost"
GOOSEFS_PORT = 9200


def example_create_table_index():
    """Create a vector or full-text index on a table."""
    print("=" * 60)
    print("Example: Create Table Index")
    print("=" * 60)
    
    with GoosefsMetastoreClient(GOOSEFS_HOST, GOOSEFS_PORT) as client:
        request = CreateTableIndexPRequest()
        request.id.extend(["my_catalog", "my_database", "my_table"])
        request.columns.extend(["embedding_vector"])
        request.index_type = "IVF_PQ"  # Index type: IVF_PQ, IVF_FLAT, etc.
        request.index_name = "idx_embedding"
        request.properties["metric_type"] = "L2"
        request.properties["num_partitions"] = "256"
        
        try:
            client.create_table_index(request)
            print(f"Index '{request.index_name}' created successfully!")
            print(f"  Columns: {list(request.columns)}")
            print(f"  Type: {request.index_type}")
        except Exception as e:
            print(f"Failed to create index: {e}")


def example_create_scalar_index():
    """Create a scalar index (e.g., B-tree) on table columns."""
    print("=" * 60)
    print("Example: Create Table Scalar Index")
    print("=" * 60)
    
    with GoosefsMetastoreClient(GOOSEFS_HOST, GOOSEFS_PORT) as client:
        request = CreateTableScalarIndexPRequest()
        request.id.extend(["my_catalog", "my_database", "my_table"])
        request.columns.extend(["user_id", "created_at"])
        request.index_type = "BTREE"  # BTREE, HASH, etc.
        
        try:
            client.create_table_scalar_index(request)
            print(f"Scalar index created successfully!")
            print(f"  Columns: {list(request.columns)}")
            print(f"  Type: {request.index_type}")
        except Exception as e:
            print(f"Failed to create scalar index: {e}")


def example_list_indices_basic():
    """List all indices on a table."""
    print("=" * 60)
    print("Example: List Table Indices (Basic)")
    print("=" * 60)
    
    with GoosefsMetastoreClient(GOOSEFS_HOST, GOOSEFS_PORT) as client:
        request = ListTableIndicesPRequest()
        request.id.extend(["my_catalog", "my_database", "my_table"])
        
        try:
            indices = client.list_table_indices(request)
            print(f"Found {len(indices)} index(es):")
            for idx in indices:
                print(f"  - {idx}")
        except Exception as e:
            print(f"Failed to list indices: {e}")


def example_list_indices_with_pagination():
    """List indices with Lance-style pagination support."""
    print("=" * 60)
    print("Example: List Table Indices (With Pagination - Lance Style)")
    print("=" * 60)
    
    with GoosefsMetastoreClient(GOOSEFS_HOST, GOOSEFS_PORT) as client:
        request = ListTableIndicesPRequest()
        request.id.extend(["my_catalog", "my_database", "my_table"])
        request.page_token = "eyJvZmZzZXQiOiAxMH0="  # Lance field - pagination token
        request.limit = 10  # Lance field - max results
        request.version = 5  # Lance field - specific table version
        
        print(f"  Table ID: {list(request.id)}")
        print(f"  Page Token: {request.page_token}")
        print(f"  Limit: {request.limit}")
        print(f"  Version: {request.version}")
        
        try:
            indices = client.list_table_indices(request)
            print(f"\n  Found {len(indices)} index(es) in this page:")
            for idx in indices:
                print(f"    - {idx}")
        except Exception as e:
            print(f"  Failed to list indices: {e}")


def example_describe_index_stats():
    """Get statistics for a specific index."""
    print("=" * 60)
    print("Example: Describe Table Index Stats")
    print("=" * 60)
    
    with GoosefsMetastoreClient(GOOSEFS_HOST, GOOSEFS_PORT) as client:
        request = DescribeTableIndexStatsPRequest()
        request.id.extend(["my_catalog", "my_database", "my_table"])
        request.index_name = "idx_embedding"
        
        try:
            stats = client.describe_table_index_stats(request)
            print(f"Index '{request.index_name}' statistics:")
            for key, value in stats.items():
                print(f"  {key}: {value}")
        except Exception as e:
            print(f"Failed to get index stats: {e}")


def example_drop_index():
    """Drop an index from a table."""
    print("=" * 60)
    print("Example: Drop Table Index")
    print("=" * 60)
    
    with GoosefsMetastoreClient(GOOSEFS_HOST, GOOSEFS_PORT) as client:
        request = DropTableIndexPRequest()
        request.id.extend(["my_catalog", "my_database", "my_table"])
        request.index_name = "idx_embedding"
        
        try:
            client.drop_table_index(request)
            print(f"Index '{request.index_name}' dropped successfully!")
        except Exception as e:
            print(f"Failed to drop index: {e}")


def main():
    """Run all index examples."""
    print()
    print("#" * 60)
    print("# Table Index Operations Examples")
    print("#" * 60)
    print()
    
    example_create_table_index()
    print()
    example_create_scalar_index()
    print()
    example_list_indices_basic()
    print()
    example_list_indices_with_pagination()
    print()
    example_describe_index_stats()
    print()
    example_drop_index()
    print()


if __name__ == "__main__":
    main()
