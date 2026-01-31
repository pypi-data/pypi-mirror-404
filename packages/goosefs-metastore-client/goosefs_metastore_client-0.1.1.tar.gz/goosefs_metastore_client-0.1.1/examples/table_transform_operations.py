"""Example: Table transformation operations.

This example demonstrates table transformation:
- transform_table: Transform a table with a definition
- get_transform_job_info: Get transformation job information
"""
from goosefs_metastore_client import GoosefsMetastoreClient

GOOSEFS_HOST = "localhost"
GOOSEFS_PORT = 9200


def example_transform_table():
    """Transform a table with a given definition."""
    print("=" * 60)
    print("Example: Transform Table")
    print("=" * 60)
    
    with GoosefsMetastoreClient(GOOSEFS_HOST, GOOSEFS_PORT) as client:
        db_name = "my_database"
        table_name = "my_table"
        definition = "COALESCE(files, 5)"  # Transformation definition
        
        print(f"  Database: {db_name}")
        print(f"  Table: {table_name}")
        print(f"  Definition: {definition}")
        
        try:
            job_id = client.transform_table(db_name, table_name, definition)
            print(f"\n  Transformation job started!")
            print(f"  Job ID: {job_id}")
        except Exception as e:
            print(f"  Transform failed: {e}")


def example_get_transform_job_info_single():
    """Get information about a specific transformation job."""
    print("=" * 60)
    print("Example: Get Transform Job Info (Single Job)")
    print("=" * 60)
    
    with GoosefsMetastoreClient(GOOSEFS_HOST, GOOSEFS_PORT) as client:
        job_id = 12345
        
        print(f"  Job ID: {job_id}")
        
        try:
            info_list = client.get_transform_job_info(job_id)
            
            if info_list:
                for info in info_list:
                    print(f"\n  Job Info:")
                    print(f"    {info}")
            else:
                print(f"  No job info found")
        except Exception as e:
            print(f"  Get job info failed: {e}")


def example_get_transform_job_info_all():
    """Get information about all transformation jobs."""
    print("=" * 60)
    print("Example: Get Transform Job Info (All Jobs)")
    print("=" * 60)
    
    with GoosefsMetastoreClient(GOOSEFS_HOST, GOOSEFS_PORT) as client:
        try:
            info_list = client.get_transform_job_info()  # No job_id = get all
            
            print(f"  Found {len(info_list)} transformation job(s)")
            
            for i, info in enumerate(info_list[:5], 1):  # Show first 5
                print(f"\n  Job {i}:")
                print(f"    {info}")
            
            if len(info_list) > 5:
                print(f"\n  ... and {len(info_list) - 5} more jobs")
        except Exception as e:
            print(f"  Get job info failed: {e}")


def example_transform_workflow():
    """Complete transformation workflow example."""
    print("=" * 60)
    print("Example: Complete Transform Workflow")
    print("=" * 60)
    
    with GoosefsMetastoreClient(GOOSEFS_HOST, GOOSEFS_PORT) as client:
        db_name = "my_database"
        table_name = "my_table"
        
        print("Step 1: Start table transformation")
        try:
            definition = "COALESCE(files, 10)"
            job_id = client.transform_table(db_name, table_name, definition)
            print(f"  Started job {job_id}")
        except Exception as e:
            print(f"  Failed to start: {e}")
            job_id = None
        
        if job_id:
            print("\nStep 2: Monitor job status")
            try:
                info_list = client.get_transform_job_info(job_id)
                if info_list:
                    print(f"  Job status: {info_list[0]}")
                else:
                    print(f"  Job not found")
            except Exception as e:
                print(f"  Monitor failed: {e}")
        
        print("\nStep 3: List all transformation jobs")
        try:
            all_jobs = client.get_transform_job_info()
            print(f"  Total jobs: {len(all_jobs)}")
        except Exception as e:
            print(f"  List failed: {e}")
        
        print()


def main():
    """Run all transformation examples."""
    print()
    print("#" * 60)
    print("# Table Transformation Operations Examples")
    print("#" * 60)
    print()
    
    example_transform_table()
    print()
    example_get_transform_job_info_single()
    print()
    example_get_transform_job_info_all()
    print()
    example_transform_workflow()
    print()


if __name__ == "__main__":
    main()
