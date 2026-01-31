"""GooseFS Metastore Client main class."""
from typing import List, Dict, Optional, Any
import logging
import uuid

import grpc
from grpc_files.table_master_pb2 import (
    GetAllDatabasesPRequest,
    GetDatabasePRequest,
    GetAllTablesPRequest,
    GetTablePRequest,
    AttachDatabasePRequest,
    DetachDatabasePRequest,
    SyncDatabasePRequest,
    MountTablePRequest,
    UnmountTablePRequest,
    AccessStatPRequest,
    IncrementHotsPRequest,
    GetTableColumnStatisticsPRequest,
    GetPartitionColumnStatisticsPRequest,
    ReadTablePRequest,
    TransformTablePRequest,
    GetTransformJobInfoPRequest,
    ListNamespacesPRequest,
    CreateNamespacePRequest,
    DescribeNamespacePRequest,
    NamespaceExistsPRequest,
    DropNamespacePRequest,
    ListTablesPRequest,
    TableExistsPRequest,
    DescribeTablePRequest,
    DeclareTablePRequest,
    DeregisterTablePRequest,
    RegisterNamespaceImplPRequest,
    UnregisterNamespaceImplPRequest,
    IsRegisteredPRequest,
    RegisterTablePRequest,
    DropTablePRequest,
    CountTableRowsPRequest,
    CreateTablePRequest,
    CreateEmptyTablePRequest,
    InsertIntoTablePRequest,
    MergeInsertIntoTablePRequest,
    UpdateTablePRequest,
    DeleteFromTablePRequest,
    QueryTablePRequest,
    CreateTableIndexPRequest,
    CreateTableScalarIndexPRequest,
    ListTableIndicesPRequest,
    DescribeTableIndexStatsPRequest,
    DropTableIndexPRequest,
    ListAllTablesPRequest,
    RestoreTablePRequest,
    RenameTablePRequest,
    ListTableVersionsPRequest,
    UpdateTableSchemaMetadataPRequest,
    GetTableStatsPRequest,
    ExplainTableQueryPlanPRequest,
    AnalyzeTableQueryPlanPRequest,
    AlterTableAddColumnsPRequest,
    AlterTableAlterColumnsPRequest,
    AlterTableDropColumnsPRequest,
    ListTableTagsPRequest,
    GetTableTagVersionPRequest,
    CreateTableTagPRequest,
    DeleteTableTagPRequest,
    UpdateTableTagPRequest,
    DescribeTransactionPRequest,
    AlterTransactionPRequest,
    Database,
    DbInfo,
    TbInfo,
    TableInfo,
    AccessStatInfo,
    SyncStatus,
)
from grpc_files.table_master_pb2_grpc import TableMasterClientServiceStub
from goosefs_metastore_client.authentication import ChannelAuthenticator, ChannelIdInjector


logger = logging.getLogger(__name__)


class GoosefsMetastoreClient:
    """User main interface with the GooseFS Table Master service via gRPC."""

    def __init__(
        self,
        host: str,
        port: int = 9200,
        max_retries: int = 3,
        timeout: int = 30,
        credentials: Optional[grpc.ChannelCredentials] = None,
        authentication_enabled: bool = True,
        username: Optional[str] = None,
        impersonation_user: Optional[str] = None,
    ) -> None:
        """
        Instantiate the client for the given host and port.

        :param host: GooseFS master host
        :param port: GooseFS table master service port (default: 9200)
        :param max_retries: maximum number of retries for failed requests
        :param timeout: timeout in seconds for gRPC calls
        :param credentials: optional gRPC credentials for secure connection
        :param authentication_enabled: whether to enable SASL authentication (default: True)
        :param username: username for authentication (defaults to OS user)
        :param impersonation_user: optional user to impersonate
        """
        self.host = host
        self.port = port
        self.max_retries = max_retries
        self.timeout = timeout
        self.credentials = credentials
        self.authentication_enabled = authentication_enabled
        self.username = username
        self.impersonation_user = impersonation_user
        self.channel: Optional[grpc.Channel] = None
        self.stub: Optional[TableMasterClientServiceStub] = None
        self.channel_id: Optional[uuid.UUID] = None

    def connect(self) -> "GoosefsMetastoreClient":
        """
        Open the gRPC connection to the GooseFS Table Master.

        :return: GoosefsMetastoreClient instance
        """
        address = f"{self.host}:{self.port}"
        
        if self.credentials:
            base_channel = grpc.secure_channel(address, self.credentials)
        else:
            base_channel = grpc.insecure_channel(address)
        
        if self.authentication_enabled:
            self.channel_id = uuid.uuid4()
            logger.info(f"Authenticating with channel ID: {self.channel_id}")
            
            # Authenticate on the base channel (without Channel ID header)
            authenticator = ChannelAuthenticator(
                base_channel,
                self.channel_id,
                username=self.username,
                impersonation_user=self.impersonation_user,
            )
            
            try:
                authenticator.authenticate()
            except Exception as e:
                base_channel.close()
                raise RuntimeError(f"Authentication failed: {e}") from e
            
            # After successful authentication, add Channel ID interceptor
            channel_id_injector = ChannelIdInjector(self.channel_id)
            self.channel = grpc.intercept_channel(base_channel, channel_id_injector)
        else:
            self.channel = base_channel
        
        self.stub = TableMasterClientServiceStub(self.channel)
        logger.info(f"Connected to GooseFS Table Master at {address}")
        
        return self

    def close(self) -> None:
        """Close the gRPC connection."""
        if self.channel:
            self.channel.close()
            logger.info("Closed connection to GooseFS Table Master")

    def __enter__(self) -> "GoosefsMetastoreClient":
        """Handle connection opening when using 'with' block statement."""
        self.connect()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Handle connection closing after the code inside 'with' block ends."""
        self.close()

    def _call_with_retry(self, func, *args, **kwargs):
        """
        Call a gRPC method with retry logic.

        :param func: the gRPC method to call
        :param args: positional arguments for the method
        :param kwargs: keyword arguments for the method
        :return: the result of the gRPC call
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return func(*args, timeout=self.timeout, **kwargs)
            except grpc.RpcError as e:
                last_exception = e
                logger.warning(
                    f"gRPC call failed (attempt {attempt + 1}/{self.max_retries}): {e}"
                )
                
                if attempt < self.max_retries - 1:
                    if e.code() in (
                        grpc.StatusCode.UNAVAILABLE,
                        grpc.StatusCode.DEADLINE_EXCEEDED,
                    ):
                        continue
                    else:
                        raise
        
        raise last_exception

    def get_all_databases(self) -> List[DbInfo]:
        """
        Get all databases from the GooseFS catalog.

        :return: list of DbInfo objects
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        request = GetAllDatabasesPRequest()
        response = self._call_with_retry(self.stub.GetAllDatabases, request)
        return list(response.dbInfo)

    def get_database(self, db_name: str) -> Database:
        """
        Get a specific database by name.

        :param db_name: database name
        :return: Database object
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        request = GetDatabasePRequest()
        request.db_name = db_name
        response = self._call_with_retry(self.stub.GetDatabase, request)
        return response.db

    def get_all_tables(self, database: str) -> List[TbInfo]:
        """
        Get all tables in a database.

        :param database: database name
        :return: list of TbInfo objects
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        request = GetAllTablesPRequest()
        request.database = database
        response = self._call_with_retry(self.stub.GetAllTables, request)
        return list(response.tbInfo)

    def get_table(self, db_name: str, table_name: str) -> TableInfo:
        """
        Get a specific table.

        :param db_name: database name
        :param table_name: table name
        :return: TableInfo object
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        request = GetTablePRequest()
        request.db_name = db_name
        request.table_name = table_name
        response = self._call_with_retry(self.stub.GetTable, request)
        return response.table_info

    def attach_database(
        self,
        udb_type: str,
        udb_db_name: str,
        db_name: str,
        configuration: Optional[Dict[str, str]] = None,
        ignore_sync_errors: bool = False,
        auto_mount: bool = False,
    ) -> SyncStatus:
        """
        Attach an external database to the GooseFS catalog.

        :param udb_type: underlying database type (e.g., "hive", "glue")
        :param udb_db_name: database name in the underlying database
        :param db_name: database name to use in GooseFS catalog
        :param configuration: configuration parameters for the database
        :param ignore_sync_errors: whether to ignore sync errors
        :param auto_mount: whether to auto-mount tables in the database
        :return: SyncStatus object
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        request = AttachDatabasePRequest()
        request.udb_type = udb_type
        request.udb_db_name = udb_db_name
        request.db_name = db_name
        request.ignore_sync_errors = ignore_sync_errors
        request.auto_mount = auto_mount
        
        if configuration:
            request.attributed.update(configuration)
        
        response = self._call_with_retry(self.stub.AttachDatabase, request)
        return response.sync_status

    def detach_database(self, db_name: str) -> bool:
        """
        Detach a database from the GooseFS catalog.

        :param db_name: database name
        :return: True if successful
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        request = DetachDatabasePRequest()
        request.db_name = db_name
        response = self._call_with_retry(self.stub.DetachDatabase, request)
        return response.success

    def sync_database(self, db_name: str) -> SyncStatus:
        """
        Sync a database with its underlying database.

        :param db_name: database name
        :return: SyncStatus object
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        request = SyncDatabasePRequest()
        request.db_name = db_name
        response = self._call_with_retry(self.stub.SyncDatabase, request)
        return response.status

    def mount_table(self, db_name: str, tb_name: str) -> bool:
        """
        Mount a table to GooseFS.

        :param db_name: database name
        :param tb_name: table name
        :return: True if successful
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        request = MountTablePRequest()
        request.dbName = db_name
        request.tbName = tb_name
        response = self._call_with_retry(self.stub.mountTable, request)
        return response.success

    def unmount_table(self, db_name: str, tb_name: str) -> bool:
        """
        Unmount a table from GooseFS.

        :param db_name: database name
        :param tb_name: table name
        :return: True if successful
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        request = UnmountTablePRequest()
        request.dbName = db_name
        request.tbName = tb_name
        response = self._call_with_retry(self.stub.unmountTable, request)
        return response.success

    def access_stat(self, days: int, top_nums: int) -> List[AccessStatInfo]:
        """
        Get access statistics for tables.

        :param days: number of days to look back
        :param top_nums: number of top results to return
        :return: list of AccessStatInfo objects
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        request = AccessStatPRequest()
        request.days = days
        request.topNums = top_nums
        response = self._call_with_retry(self.stub.accessStat, request)
        return list(response.accessStatInfo)

    def increment_hots(
        self,
        hive_hots_path_list: Optional[List[Dict[str, str]]] = None,
        presto_hots_path_list: Optional[List[Dict[str, str]]] = None,
        engine_name: Optional[str] = None,
    ) -> None:
        """
        Increment hot statistics for tables.

        :param hive_hots_path_list: list of hive hot paths
        :param presto_hots_path_list: list of presto hot paths
        :param engine_name: engine name
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        request = IncrementHotsPRequest()
        
        if engine_name:
            request.engine_name = engine_name
        
        self._call_with_retry(self.stub.incrementHots, request)

    def get_table_column_statistics(
        self, db_name: str, table_name: str, col_names: List[str]
    ) -> Any:
        """
        Get column statistics for a table.

        :param db_name: database name
        :param table_name: table name
        :param col_names: list of column names
        :return: column statistics
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        request = GetTableColumnStatisticsPRequest()
        request.db_name = db_name
        request.table_name = table_name
        request.col_names.extend(col_names)
        response = self._call_with_retry(self.stub.GetTableColumnStatistics, request)
        return list(response.statistics)

    def get_partition_column_statistics(
        self,
        db_name: str,
        table_name: str,
        col_names: List[str],
        part_names: List[str],
    ) -> Any:
        """
        Get partition column statistics.

        :param db_name: database name
        :param table_name: table name
        :param col_names: list of column names
        :param part_names: list of partition names
        :return: partition column statistics
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        request = GetPartitionColumnStatisticsPRequest()
        request.db_name = db_name
        request.table_name = table_name
        request.col_names.extend(col_names)
        request.part_names.extend(part_names)
        response = self._call_with_retry(
            self.stub.GetPartitionColumnStatistics, request
        )
        return response.partition_statistics

    def read_table(
        self, db_name: str, table_name: str, constraint: Optional[Any] = None
    ) -> Any:
        """
        Read table partitions with optional constraints.

        :param db_name: database name
        :param table_name: table name
        :param constraint: optional constraint for filtering
        :return: list of partitions
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        request = ReadTablePRequest()
        request.db_name = db_name
        request.table_name = table_name
        
        if constraint:
            request.constraint.CopyFrom(constraint)
        
        response = self._call_with_retry(self.stub.ReadTable, request)
        return list(response.partitions)

    def transform_table(
        self, db_name: str, table_name: str, definition: str
    ) -> int:
        """
        Transform a table with the given definition.

        :param db_name: database name
        :param table_name: table name
        :param definition: transformation definition
        :return: job ID for the transformation
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        request = TransformTablePRequest()
        request.db_name = db_name
        request.table_name = table_name
        request.definition = definition
        response = self._call_with_retry(self.stub.TransformTable, request)
        return response.job_id

    def get_transform_job_info(self, job_id: Optional[int] = None) -> Any:
        """
        Get information about transformation jobs.

        :param job_id: optional job ID; if not provided, returns all jobs
        :return: list of transformation job info
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        request = GetTransformJobInfoPRequest()
        
        if job_id is not None:
            request.job_id = job_id
        
        response = self._call_with_retry(self.stub.GetTransformJobInfo, request)
        return list(response.info)

    # The following method refers to the lance namespace interface.

    def list_namespaces(self, request: ListNamespacesPRequest) -> Dict[str, Any]:
        """
        List namespaces.

        :param request: ListNamespacesPRequest with id, page_token, and limit
        :return: dict with 'namespaces' list and optional 'page_token'
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        response = self._call_with_retry(self.stub.ListNamespaces, request)
        result = {"namespaces": list(response.namespaces)}
        if response.HasField("page_token"):
            result["page_token"] = response.page_token
        return result

    def create_namespace(self, request: CreateNamespacePRequest) -> Dict[str, str]:
        """
        Create a namespace.

        :param request: CreateNamespacePRequest with id, properties, and mode
        :return: response properties
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        response = self._call_with_retry(self.stub.CreateNamespace, request)
        return dict(response.properties)

    def describe_namespace(self, request: DescribeNamespacePRequest) -> Dict[str, str]:
        """
        Describe a namespace.

        :param request: DescribeNamespacePRequest with id
        :return: namespace properties
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        response = self._call_with_retry(self.stub.DescribeNamespace, request)
        return dict(response.properties)

    def namespace_exists(self, request: NamespaceExistsPRequest) -> bool:
        """
        Check if a namespace exists.

        :param request: NamespaceExistsPRequest with id
        :return: True if namespace exists
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        response = self._call_with_retry(self.stub.NamespaceExists, request)
        return response.exists

    def drop_namespace(self, request: DropNamespacePRequest) -> Dict[str, str]:
        """
        Drop a namespace.

        :param request: DropNamespacePRequest with id, mode, and behavior
        :return: response properties
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        response = self._call_with_retry(self.stub.DropNamespace, request)
        return dict(response.properties)

    def list_tables(self, request: ListTablesPRequest) -> Dict[str, Any]:
        """
        List tables in a namespace.

        :param request: ListTablesPRequest with id, page_token, and limit
        :return: dict with 'tables' list and optional 'page_token'
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        response = self._call_with_retry(self.stub.ListTables, request)
        result = {"tables": list(response.tables)}
        if response.HasField("page_token"):
            result["page_token"] = response.page_token
        return result

    def table_exists(self, request: TableExistsPRequest) -> bool:
        """
        Check if a table exists.

        :param request: TableExistsPRequest with id
        :return: True if table exists
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        response = self._call_with_retry(self.stub.TableExists, request)
        return response.exists

    def describe_table(self, request: DescribeTablePRequest) -> Dict[str, Any]:
        """
        Describe a table.

        :param request: DescribeTablePRequest with id, version, and load_detailed_metadata
        :return: table description with location and storage_options
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        response = self._call_with_retry(self.stub.DescribeTable, request)
        result = {}
        if response.HasField("location"):
            result["location"] = response.location
        result["storage_options"] = dict(response.storage_options)
        return result

    def declare_table(self, request: DeclareTablePRequest) -> Dict[str, Any]:
        """
        Declare a table.

        :param request: DeclareTablePRequest with id, location, and properties
        :return: declaration response with location and storage_options
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        response = self._call_with_retry(self.stub.DeclareTable, request)
        result = {}
        if response.HasField("location"):
            result["location"] = response.location
        result["storage_options"] = dict(response.storage_options)
        return result

    def deregister_table(self, request: DeregisterTablePRequest) -> Dict[str, Any]:
        """
        Deregister a table.

        :param request: DeregisterTablePRequest with id
        :return: deregistration response
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        response = self._call_with_retry(self.stub.DeregisterTable, request)
        result = {"id": list(response.id)}
        if response.HasField("location"):
            result["location"] = response.location
        result["properties"] = dict(response.properties)
        return result

    def register_namespace_impl(self, name: str, class_name: str) -> None:
        """
        Register a namespace implementation.

        :param name: namespace name
        :param class_name: implementation class name
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        request = RegisterNamespaceImplPRequest()
        request.name = name
        request.class_name = class_name
        
        self._call_with_retry(self.stub.RegisterNamespaceImpl, request)

    def unregister_namespace_impl(self, name: str) -> bool:
        """
        Unregister a namespace implementation.

        :param name: namespace name
        :return: True if successful
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        request = UnregisterNamespaceImplPRequest()
        request.name = name
        
        response = self._call_with_retry(self.stub.UnregisterNamespaceImpl, request)
        return response.success

    def is_registered(self, name: str) -> bool:
        """
        Check if a namespace implementation is registered.

        :param name: namespace name
        :return: True if registered
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        request = IsRegisteredPRequest()
        request.name = name
        
        response = self._call_with_retry(self.stub.IsRegistered, request)
        return response.registered

    def register_table(self, request: RegisterTablePRequest) -> Dict[str, Any]:
        """
        Register a table.

        :param request: RegisterTablePRequest with id, location, and properties
        :return: registration response with location and storage_options
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        response = self._call_with_retry(self.stub.RegisterTable, request)
        result = {}
        if response.HasField("location"):
            result["location"] = response.location
        result["storage_options"] = dict(response.storage_options)
        return result

    def drop_table(self, request: DropTablePRequest) -> None:
        """
        Drop a table.

        :param request: DropTablePRequest with id and mode
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        self._call_with_retry(self.stub.DropTable, request)

    def count_table_rows(self, request: CountTableRowsPRequest) -> int:
        """
        Count rows in a table.

        :param request: CountTableRowsPRequest with id
        :return: row count
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        response = self._call_with_retry(self.stub.CountTableRows, request)
        return response.count

    def create_table(self, request: CreateTablePRequest, request_data: Optional[Any] = None) -> Dict[str, Any]:
        """
        Create a table.

        :param request: CreateTablePRequest with id, schema, location, mode, and properties
        :param request_data: Optional additional data for table creation
        :return: creation response with location and storage_options
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        response = self._call_with_retry(self.stub.CreateTable, request)
        result = {}
        if response.HasField("location"):
            result["location"] = response.location
        result["storage_options"] = dict(response.storage_options)
        return result

    def create_empty_table(self, request: CreateEmptyTablePRequest) -> Dict[str, Any]:
        """
        Create an empty table.

        :param request: CreateEmptyTablePRequest with id, schema, location, mode, and properties
        :return: creation response with location and storage_options
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        response = self._call_with_retry(self.stub.CreateEmptyTable, request)
        result = {}
        if response.HasField("location"):
            result["location"] = response.location
        result["storage_options"] = dict(response.storage_options)
        return result

    def insert_into_table(self, request: InsertIntoTablePRequest, request_data: Optional[Any] = None) -> int:
        """
        Insert data into a table.

        :param request: InsertIntoTablePRequest with id, data, and mode
        :param request_data: Optional additional data for insertion
        :return: number of rows affected
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        response = self._call_with_retry(self.stub.InsertIntoTable, request)
        return response.rows_affected

    def merge_insert_into_table(self, request: MergeInsertIntoTablePRequest, request_data: Optional[Any] = None) -> int:
        """
        Merge insert data into a table.

        :param request: MergeInsertIntoTablePRequest with id, data, and on_columns
        :param request_data: Optional additional data for merge
        :return: number of rows affected
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        response = self._call_with_retry(self.stub.MergeInsertIntoTable, request)
        return response.rows_affected

    def update_table(self, request: UpdateTablePRequest) -> int:
        """
        Update table records.

        :param request: UpdateTablePRequest with id, updates, and where_clause
        :return: number of rows affected
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        response = self._call_with_retry(self.stub.UpdateTable, request)
        return response.rows_affected

    def delete_from_table(self, request: DeleteFromTablePRequest) -> int:
        """
        Delete records from a table.

        :param request: DeleteFromTablePRequest with id and where_clause
        :return: number of rows affected
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        response = self._call_with_retry(self.stub.DeleteFromTable, request)
        return response.rows_affected

    def query_table(self, request: QueryTablePRequest) -> str:
        """
        Query a table.

        :param request: QueryTablePRequest with id, query, and limit
        :return: query result
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        response = self._call_with_retry(self.stub.QueryTable, request)
        return response.result

    def create_table_index(self, request: CreateTableIndexPRequest) -> None:
        """
        Create a table index.

        :param request: CreateTableIndexPRequest with id, columns, index_type, and index_name
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        self._call_with_retry(self.stub.CreateTableIndex, request)

    def create_table_scalar_index(self, request: CreateTableScalarIndexPRequest) -> None:
        """
        Create a table scalar index.

        :param request: CreateTableScalarIndexPRequest with id, columns, and index_type
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        self._call_with_retry(self.stub.CreateTableScalarIndex, request)

    def list_table_indices(self, request: ListTableIndicesPRequest) -> List[str]:
        """
        List table indices.

        :param request: ListTableIndicesPRequest with id
        :return: list of index names
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        response = self._call_with_retry(self.stub.ListTableIndices, request)
        return list(response.indices)

    def describe_table_index_stats(self, request: DescribeTableIndexStatsPRequest) -> Dict[str, str]:
        """
        Describe table index statistics.

        :param request: DescribeTableIndexStatsPRequest with id and index_name
        :return: index statistics
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        response = self._call_with_retry(self.stub.DescribeTableIndexStats, request)
        return dict(response.stats)

    def drop_table_index(self, request: DropTableIndexPRequest) -> None:
        """
        Drop a table index.

        :param request: DropTableIndexPRequest with id and index_name
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        self._call_with_retry(self.stub.DropTableIndex, request)

    def list_all_tables(self, request: ListAllTablesPRequest) -> Dict[str, Any]:
        """
        List all tables.

        :param request: ListAllTablesPRequest with page_token and limit
        :return: dict with 'tables' list and optional 'page_token'
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        response = self._call_with_retry(self.stub.ListAllTables, request)
        result = {"tables": list(response.tables)}
        if response.HasField("page_token"):
            result["page_token"] = response.page_token
        return result

    def restore_table(self, request: RestoreTablePRequest) -> None:
        """
        Restore a table to a specific version.

        :param request: RestoreTablePRequest with id and version
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        self._call_with_retry(self.stub.RestoreTable, request)

    def rename_table(self, request: RenameTablePRequest) -> None:
        """
        Rename a table.

        :param request: RenameTablePRequest with old_id and new_id
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        self._call_with_retry(self.stub.RenameTable, request)

    def list_table_versions(self, request: ListTableVersionsPRequest) -> List[int]:
        """
        List table versions.

        :param request: ListTableVersionsPRequest with id
        :return: list of version numbers
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        response = self._call_with_retry(self.stub.ListTableVersions, request)
        return list(response.versions)

    def update_table_schema_metadata(self, request: UpdateTableSchemaMetadataPRequest) -> None:
        """
        Update table schema metadata.

        :param request: UpdateTableSchemaMetadataPRequest with id and schema
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        self._call_with_retry(self.stub.UpdateTableSchemaMetadata, request)

    def get_table_stats(self, request: GetTableStatsPRequest) -> Dict[str, str]:
        """
        Get table statistics.

        :param request: GetTableStatsPRequest with id
        :return: table statistics
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        response = self._call_with_retry(self.stub.GetTableStats, request)
        return dict(response.stats)

    def explain_table_query_plan(self, request: ExplainTableQueryPlanPRequest) -> str:
        """
        Explain table query plan.

        :param request: ExplainTableQueryPlanPRequest with id and query
        :return: query plan explanation
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        response = self._call_with_retry(self.stub.ExplainTableQueryPlan, request)
        return response.plan

    def analyze_table_query_plan(self, request: AnalyzeTableQueryPlanPRequest) -> str:
        """
        Analyze table query plan.

        :param request: AnalyzeTableQueryPlanPRequest with id and query
        :return: query plan analysis
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        response = self._call_with_retry(self.stub.AnalyzeTableQueryPlan, request)
        return response.analysis

    def alter_table_add_columns(self, request: AlterTableAddColumnsPRequest) -> None:
        """
        Add columns to a table.

        :param request: AlterTableAddColumnsPRequest with id and columns
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        self._call_with_retry(self.stub.AlterTableAddColumns, request)

    def alter_table_alter_columns(self, request: AlterTableAlterColumnsPRequest) -> None:
        """
        Alter columns in a table.

        :param request: AlterTableAlterColumnsPRequest with id and columns
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        self._call_with_retry(self.stub.AlterTableAlterColumns, request)

    def alter_table_drop_columns(self, request: AlterTableDropColumnsPRequest) -> None:
        """
        Drop columns from a table.

        :param request: AlterTableDropColumnsPRequest with id and columns
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        self._call_with_retry(self.stub.AlterTableDropColumns, request)

    def list_table_tags(self, request: ListTableTagsPRequest) -> List[str]:
        """
        List table tags.

        :param request: ListTableTagsPRequest with id
        :return: list of tag names
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        response = self._call_with_retry(self.stub.ListTableTags, request)
        return list(response.tags)

    def get_table_tag_version(self, request: GetTableTagVersionPRequest) -> int:
        """
        Get table tag version.

        :param request: GetTableTagVersionPRequest with id and tag
        :return: tag version
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        response = self._call_with_retry(self.stub.GetTableTagVersion, request)
        return response.version

    def create_table_tag(self, request: CreateTableTagPRequest) -> None:
        """
        Create a table tag.

        :param request: CreateTableTagPRequest with id, tag, and version
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        self._call_with_retry(self.stub.CreateTableTag, request)

    def delete_table_tag(self, request: DeleteTableTagPRequest) -> None:
        """
        Delete a table tag.

        :param request: DeleteTableTagPRequest with id and tag
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        self._call_with_retry(self.stub.DeleteTableTag, request)

    def update_table_tag(self, request: UpdateTableTagPRequest) -> None:
        """
        Update a table tag.

        :param request: UpdateTableTagPRequest with id, tag, and version
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        self._call_with_retry(self.stub.UpdateTableTag, request)

    def describe_transaction(self, request: DescribeTransactionPRequest) -> Dict[str, str]:
        """
        Describe a transaction.

        :param request: DescribeTransactionPRequest with transaction_id
        :return: transaction properties
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        response = self._call_with_retry(self.stub.DescribeTransaction, request)
        return dict(response.properties)

    def alter_transaction(self, request: AlterTransactionPRequest) -> None:
        """
        Alter a transaction.

        :param request: AlterTransactionPRequest with transaction_id and action
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        self._call_with_retry(self.stub.AlterTransaction, request)
