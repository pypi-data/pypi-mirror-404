"""Example: Namespace operations including Lance/GooseFS compatible styles.

This example demonstrates namespace-related operations:
- list_namespaces: List namespaces with pagination
- create_namespace: Create a new namespace
- describe_namespace: Get namespace details
- namespace_exists: Check if namespace exists
- drop_namespace: Drop a namespace
"""
from goosefs_metastore_client import GoosefsMetastoreClient
from grpc_files.table_master_pb2 import (
    ListNamespacesPRequest,
    CreateNamespacePRequest,
    DescribeNamespacePRequest,
    NamespaceExistsPRequest,
    DropNamespacePRequest,
)

GOOSEFS_HOST = "localhost"
GOOSEFS_PORT = 9200


def example_list_namespaces():
    """List namespaces with pagination support."""
    print("=" * 60)
    print("Example: List Namespaces")
    print("=" * 60)
    
    with GoosefsMetastoreClient(GOOSEFS_HOST, GOOSEFS_PORT) as client:
        # Basic listing
        request = ListNamespacesPRequest()
        request.id.extend(["my_catalog"])
        
        result = client.list_namespaces(request)
        print(f"Found {len(result['namespaces'])} namespace(s)")
        for ns in result["namespaces"]:
            print(f"  - {ns}")
        
        # With pagination (Lance style)
        request_with_page = ListNamespacesPRequest()
        request_with_page.id.extend(["my_catalog"])
        request_with_page.page_token = ""  # First page
        request_with_page.limit = 10
        
        result = client.list_namespaces(request_with_page)
        print(f"\nWith pagination (limit=10):")
        print(f"  Namespaces: {len(result['namespaces'])}")
        if "page_token" in result:
            print(f"  Next page token: {result['page_token']}")


def example_create_namespace():
    """Create a namespace with properties."""
    print("=" * 60)
    print("Example: Create Namespace")
    print("=" * 60)
    
    with GoosefsMetastoreClient(GOOSEFS_HOST, GOOSEFS_PORT) as client:
        request = CreateNamespacePRequest()
        request.id.extend(["my_catalog", "new_namespace"])
        request.properties["owner"] = "admin"
        request.properties["description"] = "Test namespace"
        request.mode = "CREATE"  # CREATE, CREATE_IF_NOT_EXISTS
        
        try:
            result = client.create_namespace(request)
            print(f"Namespace created successfully!")
            print(f"Properties: {result}")
        except Exception as e:
            print(f"Failed to create namespace: {e}")


def example_describe_namespace():
    """Describe a namespace to get its properties."""
    print("=" * 60)
    print("Example: Describe Namespace")
    print("=" * 60)
    
    with GoosefsMetastoreClient(GOOSEFS_HOST, GOOSEFS_PORT) as client:
        request = DescribeNamespacePRequest()
        request.id.extend(["my_catalog", "my_namespace"])
        
        try:
            properties = client.describe_namespace(request)
            print(f"Namespace properties:")
            for key, value in properties.items():
                print(f"  {key}: {value}")
        except Exception as e:
            print(f"Failed to describe namespace: {e}")


def example_namespace_exists():
    """Check if a namespace exists."""
    print("=" * 60)
    print("Example: Namespace Exists")
    print("=" * 60)
    
    with GoosefsMetastoreClient(GOOSEFS_HOST, GOOSEFS_PORT) as client:
        request = NamespaceExistsPRequest()
        request.id.extend(["my_catalog", "my_namespace"])
        
        exists = client.namespace_exists(request)
        print(f"Namespace exists: {exists}")


def example_drop_namespace():
    """Drop a namespace."""
    print("=" * 60)
    print("Example: Drop Namespace")
    print("=" * 60)
    
    with GoosefsMetastoreClient(GOOSEFS_HOST, GOOSEFS_PORT) as client:
        request = DropNamespacePRequest()
        request.id.extend(["my_catalog", "namespace_to_drop"])
        request.mode = "DROP"  # DROP, DROP_IF_EXISTS
        request.behavior = "RESTRICT"  # RESTRICT, CASCADE
        
        try:
            result = client.drop_namespace(request)
            print(f"Namespace dropped successfully!")
            print(f"Properties: {result}")
        except Exception as e:
            print(f"Failed to drop namespace: {e}")


def main():
    """Run all namespace examples."""
    print()
    print("#" * 60)
    print("# Namespace Operations Examples")
    print("#" * 60)
    print()
    
    example_list_namespaces()
    print()
    example_create_namespace()
    print()
    example_describe_namespace()
    print()
    example_namespace_exists()
    print()
    example_drop_namespace()
    print()


if __name__ == "__main__":
    main()
