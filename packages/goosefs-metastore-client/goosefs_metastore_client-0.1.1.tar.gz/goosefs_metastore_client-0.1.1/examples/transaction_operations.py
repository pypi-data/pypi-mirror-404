"""Example: Transaction operations with Lance/GooseFS compatible styles.

This example demonstrates transaction management:
- describe_transaction: Describe a transaction (Lance id / GooseFS transaction_id)
- alter_transaction: Alter transaction state
"""
from goosefs_metastore_client import GoosefsMetastoreClient
from grpc_files.table_master_pb2 import (
    DescribeTransactionPRequest,
    AlterTransactionPRequest,
)

GOOSEFS_HOST = "localhost"
GOOSEFS_PORT = 9200


def example_describe_transaction_lance_style():
    """Describe a transaction using Lance style id field."""
    print("=" * 60)
    print("Example: Describe Transaction - Lance Style")
    print("=" * 60)
    
    with GoosefsMetastoreClient(GOOSEFS_HOST, GOOSEFS_PORT) as client:
        request = DescribeTransactionPRequest()
        request.id.extend(["txn_12345"])  # Lance field
        
        print(f"  ID (Lance): {list(request.id)}")
        
        try:
            properties = client.describe_transaction(request)
            print(f"  Transaction properties:")
            for key, value in properties.items():
                print(f"    {key}: {value}")
        except Exception as e:
            print(f"  Failed: {e}")


def example_describe_transaction_goosefs_style():
    """Describe a transaction using GooseFS style transaction_id field."""
    print("=" * 60)
    print("Example: Describe Transaction - GooseFS Style")
    print("=" * 60)
    
    with GoosefsMetastoreClient(GOOSEFS_HOST, GOOSEFS_PORT) as client:
        request = DescribeTransactionPRequest()
        request.transaction_id = "txn_12345"  # GooseFS field
        
        print(f"  Transaction ID (GooseFS): {request.transaction_id}")
        
        try:
            properties = client.describe_transaction(request)
            print(f"  Transaction properties:")
            for key, value in properties.items():
                print(f"    {key}: {value}")
        except Exception as e:
            print(f"  Failed: {e}")


def example_alter_transaction():
    """Alter a transaction state."""
    print("=" * 60)
    print("Example: Alter Transaction")
    print("=" * 60)
    
    with GoosefsMetastoreClient(GOOSEFS_HOST, GOOSEFS_PORT) as client:
        # Commit a transaction
        commit_request = AlterTransactionPRequest()
        commit_request.transaction_id = "txn_12345"
        commit_request.action = "COMMIT"  # COMMIT, ROLLBACK, ABORT
        
        print(f"  Transaction: {commit_request.transaction_id}")
        print(f"  Action: {commit_request.action}")
        
        try:
            client.alter_transaction(commit_request)
            print(f"  Transaction committed successfully!")
        except Exception as e:
            print(f"  Commit failed: {e}")


def main():
    """Run all transaction examples."""
    print()
    print("#" * 60)
    print("# Transaction Operations Examples")
    print("#" * 60)
    print()
    
    example_describe_transaction_lance_style()
    print()
    example_describe_transaction_goosefs_style()
    print()
    example_alter_transaction()
    print()


if __name__ == "__main__":
    main()
