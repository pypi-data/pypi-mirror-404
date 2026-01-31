"""Example: Table tag operations.

This example demonstrates table tagging:
- list_table_tags: List all tags on a table
- get_table_tag_version: Get version for a specific tag
- create_table_tag: Create a new tag
- update_table_tag: Update an existing tag
- delete_table_tag: Delete a tag
"""
from goosefs_metastore_client import GoosefsMetastoreClient
from grpc_files.table_master_pb2 import (
    ListTableTagsPRequest,
    GetTableTagVersionPRequest,
    CreateTableTagPRequest,
    UpdateTableTagPRequest,
    DeleteTableTagPRequest,
)

GOOSEFS_HOST = "localhost"
GOOSEFS_PORT = 9200


def example_list_tags():
    """List all tags on a table."""
    print("=" * 60)
    print("Example: List Table Tags")
    print("=" * 60)
    
    with GoosefsMetastoreClient(GOOSEFS_HOST, GOOSEFS_PORT) as client:
        request = ListTableTagsPRequest()
        request.id.extend(["my_catalog", "my_database", "my_table"])
        
        try:
            tags = client.list_table_tags(request)
            print(f"Found {len(tags)} tag(s):")
            for tag in tags:
                print(f"  - {tag}")
        except Exception as e:
            print(f"Failed to list tags: {e}")


def example_get_tag_version():
    """Get the version associated with a specific tag."""
    print("=" * 60)
    print("Example: Get Table Tag Version")
    print("=" * 60)
    
    with GoosefsMetastoreClient(GOOSEFS_HOST, GOOSEFS_PORT) as client:
        request = GetTableTagVersionPRequest()
        request.id.extend(["my_catalog", "my_database", "my_table"])
        request.tag = "v1.0.0"
        
        try:
            version = client.get_table_tag_version(request)
            print(f"Tag '{request.tag}' points to version {version}")
        except Exception as e:
            print(f"Failed to get tag version: {e}")


def example_create_tag():
    """Create a new tag on a table."""
    print("=" * 60)
    print("Example: Create Table Tag")
    print("=" * 60)
    
    with GoosefsMetastoreClient(GOOSEFS_HOST, GOOSEFS_PORT) as client:
        request = CreateTableTagPRequest()
        request.id.extend(["my_catalog", "my_database", "my_table"])
        request.tag = "release-2024-01"
        request.version = 10  # Tag this version
        
        print(f"  Creating tag '{request.tag}' for version {request.version}")
        
        try:
            client.create_table_tag(request)
            print(f"  Tag created successfully!")
        except Exception as e:
            print(f"  Create tag failed: {e}")


def example_update_tag():
    """Update an existing tag to point to a different version."""
    print("=" * 60)
    print("Example: Update Table Tag")
    print("=" * 60)
    
    with GoosefsMetastoreClient(GOOSEFS_HOST, GOOSEFS_PORT) as client:
        request = UpdateTableTagPRequest()
        request.id.extend(["my_catalog", "my_database", "my_table"])
        request.tag = "latest"
        request.version = 15  # Update to point to version 15
        
        print(f"  Updating tag '{request.tag}' to version {request.version}")
        
        try:
            client.update_table_tag(request)
            print(f"  Tag updated successfully!")
        except Exception as e:
            print(f"  Update tag failed: {e}")


def example_delete_tag():
    """Delete a tag from a table."""
    print("=" * 60)
    print("Example: Delete Table Tag")
    print("=" * 60)
    
    with GoosefsMetastoreClient(GOOSEFS_HOST, GOOSEFS_PORT) as client:
        request = DeleteTableTagPRequest()
        request.id.extend(["my_catalog", "my_database", "my_table"])
        request.tag = "deprecated-tag"
        
        print(f"  Deleting tag '{request.tag}'")
        
        try:
            client.delete_table_tag(request)
            print(f"  Tag deleted successfully!")
        except Exception as e:
            print(f"  Delete tag failed: {e}")


def main():
    """Run all tag examples."""
    print()
    print("#" * 60)
    print("# Table Tag Operations Examples")
    print("#" * 60)
    print()
    
    example_list_tags()
    print()
    example_get_tag_version()
    print()
    example_create_tag()
    print()
    example_update_tag()
    print()
    example_delete_tag()
    print()


if __name__ == "__main__":
    main()
