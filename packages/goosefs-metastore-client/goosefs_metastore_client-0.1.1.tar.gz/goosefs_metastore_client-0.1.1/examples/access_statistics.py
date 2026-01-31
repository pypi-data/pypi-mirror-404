"""Example: Get access statistics for tables."""
from goosefs_metastore_client import GoosefsMetastoreClient

GOOSEFS_HOST = "localhost"
GOOSEFS_PORT = 9200

with GoosefsMetastoreClient(GOOSEFS_HOST, GOOSEFS_PORT) as client:
    stats = client.access_stat(days=7, top_nums=10)
    
    print(f"Top {len(stats)} accessed tables in the last 7 days:")
    for i, stat in enumerate(stats, 1):
        print(f"{i}. {stat.db_name}.{stat.tb_name}")
        print(f"   Hot Count: {stat.hots}")
        print(f"   Is Mounted: {stat.is_mount}")
        print()
