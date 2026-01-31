# GooseFS Metastore Client

A Python client library for connecting to GooseFS Table Master service via gRPC protocol.

## Overview

GooseFS Metastore Client provides a Python interface to interact with GooseFS's Table Master service, enabling you to manage databases and tables in the GooseFS catalog. 

## Architecture

The client follows this call flow:

```
Python Client (GoosefsMetastoreClient)
    ↓
gRPC Client (TableMasterClientServiceStub)
    ↓
[gRPC Network Call]
    ↓
GooseFS Master (TableMasterClientServiceHandler)
    ↓
DefaultTableMaster
```

## Features

- List and retrieve databases and tables from GooseFS catalog
- Attach external databases (e.g., from Hive) to GooseFS
- Mount/unmount tables for caching in GooseFS
- Synchronize databases with underlying metadata stores
- Retrieve table access statistics
- Get table and partition column statistics
- Transform tables with custom definitions

## Installation

```bash
pip install -e .
```

## Requirements

- Python >= 3.7
- grpcio >= 1.50.0
- protobuf >= 3.20.0
- A running GooseFS cluster with Table Master service enabled

## Quick Start

### Basic Usage

```python
from goosefs_metastore_client import GoosefsMetastoreClient

GOOSEFS_HOST = "localhost"
GOOSEFS_PORT = 9200

with GoosefsMetastoreClient(GOOSEFS_HOST, GOOSEFS_PORT) as client:
    databases = client.get_all_databases()
    for db_info in databases:
        print(f"Database: {db_info.name}")
```

### List Databases

```python
from goosefs_metastore_client import GoosefsMetastoreClient

with GoosefsMetastoreClient("localhost", 9200) as client:
    databases = client.get_all_databases()
    for db in databases:
        print(f"{db.name} - Type: {db.type}")
```

### Get Database Details

```python
from goosefs_metastore_client import GoosefsMetastoreClient

with GoosefsMetastoreClient("localhost", 9200) as client:
    database = client.get_database("my_database")
    print(f"Location: {database.location}")
    print(f"Owner: {database.owner_name}")
```

### Attach External Database

```python
from goosefs_metastore_client import GoosefsMetastoreClient

with GoosefsMetastoreClient("localhost", 9200) as client:
    sync_status = client.attach_database(
        udb_type="hive",
        udb_db_name="hive_db",
        db_name="goosefs_db",
        configuration={
            "hive.metastore.uris": "thrift://hive-metastore:9083",
        },
        auto_mount=True,
    )
    print(f"Tables synced: {len(sync_status.tables_updated)}")
```

### List and Get Tables

```python
from goosefs_metastore_client import GoosefsMetastoreClient

with GoosefsMetastoreClient("localhost", 9200) as client:
    tables = client.get_all_tables("my_database")
    for table in tables:
        print(f"Table: {table.name}, Mounted: {table.is_mount}")
    
    table_info = client.get_table("my_database", "my_table")
    print(f"Owner: {table_info.owner}")
    for col in table_info.schema.cols:
        print(f"Column: {col.name} ({col.type})")
```

### Mount/Unmount Tables

```python
from goosefs_metastore_client import GoosefsMetastoreClient

with GoosefsMetastoreClient("localhost", 9200) as client:
    client.mount_table("my_database", "my_table")
    print("Table mounted for caching")
    
    client.unmount_table("my_database", "my_table")
    print("Table unmounted")
```

### Access Statistics

```python
from goosefs_metastore_client import GoosefsMetastoreClient

with GoosefsMetastoreClient("localhost", 9200) as client:
    stats = client.access_stat(days=7, top_nums=10)
    for stat in stats:
        print(f"{stat.db_name}.{stat.tb_name}: {stat.hots} accesses")
```

## Using Builders

The client provides builder classes to construct database and table objects:

```python
from goosefs_metastore_client.builders import DatabaseBuilder, TableBuilder, FieldSchemaBuilder

database = DatabaseBuilder(
    db_name="my_database",
    description="My test database",
    location="/user/hive/warehouse/my_database.db",
    owner_name="admin",
    parameters={"key": "value"},
).build()
```

## API Reference

### GoosefsMetastoreClient

Main client class for interacting with GooseFS Table Master.

#### Database Operations

- `get_all_databases()` - Get all databases in the catalog
- `get_database(db_name)` - Get a specific database by name
- `attach_database(udb_type, udb_db_name, db_name, ...)` - Attach an external database
- `detach_database(db_name)` - Detach a database from the catalog
- `sync_database(db_name)` - Sync a database with its underlying store

#### Table Operations

- `get_all_tables(database)` - Get all tables in a database
- `get_table(db_name, table_name)` - Get a specific table
- `mount_table(db_name, tb_name)` - Mount a table to GooseFS
- `unmount_table(db_name, tb_name)` - Unmount a table from GooseFS

#### Statistics and Analytics

- `access_stat(days, top_nums)` - Get table access statistics
- `get_table_column_statistics(db_name, table_name, col_names)` - Get column statistics
- `get_partition_column_statistics(db_name, table_name, col_names, part_names)` - Get partition statistics

#### Advanced Operations

- `read_table(db_name, table_name, constraint)` - Read table partitions with constraints
- `transform_table(db_name, table_name, definition)` - Transform a table
- `get_transform_job_info(job_id)` - Get transformation job information

## Configuration

### Connection Parameters

- `host`: GooseFS master hostname
- `port`: Table Master client service port (default: 9200)
- `max_retries`: Maximum retry attempts for failed requests (default: 3)
- `timeout`: Timeout in seconds for gRPC calls (default: 30)
- `credentials`: Optional gRPC credentials for secure connections

### Example with Custom Configuration

```python
client = GoosefsMetastoreClient(
    host="goosefs-master.example.com",
    port=9200,
    max_retries=5,
    timeout=60,
)
client.connect()
try:
    databases = client.get_all_databases()
finally:
    client.close()
```

## Development

### Setup Development Environment

```bash
pip install -r requirements.dev.txt
```

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black goosefs_metastore_client/
```

### Linting

```bash
flake8 goosefs_metastore_client/
mypy goosefs_metastore_client/
```

## Project Structure

```
goosefs-metastore-client/
├── goosefs_metastore_client/
│   ├── __init__.py
│   ├── goosefs_metastore_client.py
│   └── builders/
│       ├── __init__.py
│       ├── abstract_builder.py
│       ├── database_builder.py
│       ├── field_schema_builder.py
│       └── table_builder.py
├── grpc_files/
│   ├── __init__.py
│   ├── common_pb2.py
│   ├── job_master_pb2.py
│   ├── table_master_pb2.py
│   ├── table_master_pb2_grpc.py
│   └── proto/
│       ├── common.proto
│       ├── job_master.proto
│       └── table_master.proto
├── examples/
│   ├── list_databases.py
│   ├── get_database.py
│   ├── attach_database.py
│   ├── list_tables.py
│   ├── get_table.py
│   ├── mount_table.py
│   └── access_statistics.py
├── tests/
│   └── unit/
│       └── goosefs_metastore_client/
│           └── builders/
├── setup.py
├── requirements.txt
└── README.md
```

## Comparison with Hive Metastore Client

| Feature | Hive Metastore Client | GooseFS Metastore Client |
|---------|----------------------|--------------------------|
| Protocol | Thrift | gRPC |
| Server | Hive Metastore | GooseFS Table Master |
| Connection | TSocket + TBinaryProtocol | gRPC Channel + Stub |
| Retry Logic | Manual | Built-in with configurable retries |
| Database Operations | Thrift API | gRPC API |
| Table Operations | Thrift API | gRPC API |

## License

Apache License 2.0

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
