"""Example: Table declaration and registration operations.

This example demonstrates table registration:
- declare_table: Declare a table with location
- register_table: Register an external table
- deregister_table: Deregister a table
- register_namespace_impl: Register namespace implementation
- unregister_namespace_impl: Unregister namespace implementation
- is_registered: Check if namespace impl is registered
"""
from goosefs_metastore_client import GoosefsMetastoreClient
from grpc_files.table_master_pb2 import (
    DeclareTablePRequest,
    RegisterTablePRequest,
    DeregisterTablePRequest,
)

GOOSEFS_HOST = "localhost"
GOOSEFS_PORT = 9200


def example_declare_table():
    """Declare a table with location and properties."""
    print("=" * 60)
    print("Example: Declare Table")
    print("=" * 60)
    
    with GoosefsMetastoreClient(GOOSEFS_HOST, GOOSEFS_PORT) as client:
        request = DeclareTablePRequest()
        request.id.extend(["my_catalog", "my_database", "declared_table"])
        request.location = "s3://my-bucket/data/declared_table"
        request.properties["format"] = "lance"
        request.properties["storage_class"] = "STANDARD"
        
        print(f"  Table ID: {list(request.id)}")
        print(f"  Location: {request.location}")
        print(f"  Properties: {dict(request.properties)}")
        
        try:
            result = client.declare_table(request)
            print(f"\n  Declaration result:")
            print(f"    Location: {result.get('location', 'N/A')}")
            print(f"    Storage Options: {result.get('storage_options', {})}")
        except Exception as e:
            print(f"  Declaration failed: {e}")


def example_register_table():
    """Register an existing external table."""
    print("=" * 60)
    print("Example: Register Table")
    print("=" * 60)
    
    with GoosefsMetastoreClient(GOOSEFS_HOST, GOOSEFS_PORT) as client:
        request = RegisterTablePRequest()
        request.id.extend(["my_catalog", "my_database", "external_table"])
        request.location = "s3://external-bucket/tables/external_table"
        request.properties["format"] = "lance"
        request.properties["read_only"] = "true"
        
        print(f"  Table ID: {list(request.id)}")
        print(f"  Location: {request.location}")
        
        try:
            result = client.register_table(request)
            print(f"\n  Registration result:")
            print(f"    Location: {result.get('location', 'N/A')}")
            print(f"    Storage Options: {result.get('storage_options', {})}")
        except Exception as e:
            print(f"  Registration failed: {e}")


def example_deregister_table():
    """Deregister a table from the catalog."""
    print("=" * 60)
    print("Example: Deregister Table")
    print("=" * 60)
    
    with GoosefsMetastoreClient(GOOSEFS_HOST, GOOSEFS_PORT) as client:
        request = DeregisterTablePRequest()
        request.id.extend(["my_catalog", "my_database", "external_table"])
        
        print(f"  Table ID: {list(request.id)}")
        
        try:
            result = client.deregister_table(request)
            print(f"\n  Deregistration result:")
            print(f"    ID: {result.get('id', [])}")
            print(f"    Location: {result.get('location', 'N/A')}")
            print(f"    Properties: {result.get('properties', {})}")
        except Exception as e:
            print(f"  Deregistration failed: {e}")


def example_register_namespace_impl():
    """Register a namespace implementation class."""
    print("=" * 60)
    print("Example: Register Namespace Implementation")
    print("=" * 60)
    
    with GoosefsMetastoreClient(GOOSEFS_HOST, GOOSEFS_PORT) as client:
        name = "lance"
        class_name = "com.example.LanceNamespaceImpl"
        
        print(f"  Name: {name}")
        print(f"  Class: {class_name}")
        
        try:
            client.register_namespace_impl(name, class_name)
            print(f"  Namespace impl registered successfully!")
        except Exception as e:
            print(f"  Registration failed: {e}")


def example_unregister_namespace_impl():
    """Unregister a namespace implementation."""
    print("=" * 60)
    print("Example: Unregister Namespace Implementation")
    print("=" * 60)
    
    with GoosefsMetastoreClient(GOOSEFS_HOST, GOOSEFS_PORT) as client:
        name = "lance"
        
        print(f"  Name: {name}")
        
        try:
            success = client.unregister_namespace_impl(name)
            print(f"  Unregister result: {success}")
        except Exception as e:
            print(f"  Unregister failed: {e}")


def example_is_registered():
    """Check if a namespace implementation is registered."""
    print("=" * 60)
    print("Example: Is Namespace Implementation Registered")
    print("=" * 60)
    
    with GoosefsMetastoreClient(GOOSEFS_HOST, GOOSEFS_PORT) as client:
        names = ["lance", "hive", "glue", "unknown"]
        
        for name in names:
            try:
                is_reg = client.is_registered(name)
                print(f"  {name}: {'Registered' if is_reg else 'Not registered'}")
            except Exception as e:
                print(f"  {name}: Error - {e}")


def main():
    """Run all registration examples."""
    print()
    print("#" * 60)
    print("# Table Declaration & Registration Examples")
    print("#" * 60)
    print()
    
    example_declare_table()
    print()
    example_register_table()
    print()
    example_deregister_table()
    print()
    example_register_namespace_impl()
    print()
    example_unregister_namespace_impl()
    print()
    example_is_registered()
    print()


if __name__ == "__main__":
    main()
