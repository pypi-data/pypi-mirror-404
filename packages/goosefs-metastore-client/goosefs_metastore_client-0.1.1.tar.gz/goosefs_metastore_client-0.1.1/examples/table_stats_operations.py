"""Example: Table statistics and query plan operations.

This example demonstrates analytics capabilities:
- get_table_stats: Get table statistics
- explain_table_query_plan: Explain query plan
- analyze_table_query_plan: Analyze query plan
"""
from goosefs_metastore_client import GoosefsMetastoreClient
from grpc_files.table_master_pb2 import (
    GetTableStatsPRequest,
    ExplainTableQueryPlanPRequest,
    AnalyzeTableQueryPlanPRequest,
)

GOOSEFS_HOST = "localhost"
GOOSEFS_PORT = 9200


def example_get_table_stats():
    """Get statistics for a table."""
    print("=" * 60)
    print("Example: Get Table Stats")
    print("=" * 60)
    
    with GoosefsMetastoreClient(GOOSEFS_HOST, GOOSEFS_PORT) as client:
        request = GetTableStatsPRequest()
        request.id.extend(["my_catalog", "my_database", "my_table"])
        
        try:
            stats = client.get_table_stats(request)
            print(f"Table statistics:")
            for key, value in stats.items():
                print(f"  {key}: {value}")
        except Exception as e:
            print(f"Failed to get stats: {e}")


def example_explain_query_plan():
    """Explain the query execution plan."""
    print("=" * 60)
    print("Example: Explain Table Query Plan")
    print("=" * 60)
    
    with GoosefsMetastoreClient(GOOSEFS_HOST, GOOSEFS_PORT) as client:
        request = ExplainTableQueryPlanPRequest()
        request.id.extend(["my_catalog", "my_database", "my_table"])
        request.query = "SELECT * FROM table WHERE age > 20 AND status = 'active'"
        
        print(f"  Query: {request.query}")
        print()
        
        try:
            plan = client.explain_table_query_plan(request)
            print(f"  Execution plan:")
            print(f"  {plan}")
        except Exception as e:
            print(f"  Failed to explain plan: {e}")


def example_analyze_query_plan():
    """Analyze the query execution plan with performance metrics."""
    print("=" * 60)
    print("Example: Analyze Table Query Plan")
    print("=" * 60)
    
    with GoosefsMetastoreClient(GOOSEFS_HOST, GOOSEFS_PORT) as client:
        request = AnalyzeTableQueryPlanPRequest()
        request.id.extend(["my_catalog", "my_database", "my_table"])
        request.query = "SELECT user_id, COUNT(*) FROM table GROUP BY user_id"
        
        print(f"  Query: {request.query}")
        print()
        
        try:
            analysis = client.analyze_table_query_plan(request)
            print(f"  Query analysis:")
            print(f"  {analysis}")
        except Exception as e:
            print(f"  Failed to analyze plan: {e}")


def main():
    """Run all statistics and query plan examples."""
    print()
    print("#" * 60)
    print("# Table Statistics & Query Plan Examples")
    print("#" * 60)
    print()
    
    example_get_table_stats()
    print()
    example_explain_query_plan()
    print()
    example_analyze_query_plan()
    print()


if __name__ == "__main__":
    main()
