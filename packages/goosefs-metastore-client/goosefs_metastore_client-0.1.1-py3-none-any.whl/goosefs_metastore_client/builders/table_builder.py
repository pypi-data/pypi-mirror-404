"""TableBuilder for GooseFS TableInfo objects."""
from typing import Dict, List, Optional

from goosefs_metastore_client.builders.abstract_builder import AbstractBuilder
from grpc_files.table_master_pb2 import (
    TableInfo,
    Schema,
    FieldSchema,
    Layout,
)


class TableBuilder(AbstractBuilder):
    """Builds gRPC TableInfo object for GooseFS."""

    def __init__(
        self,
        table_name: str,
        db_name: str,
        owner: Optional[str] = None,
        schema: Optional[Schema] = None,
        partition_cols: Optional[List[FieldSchema]] = None,
        parameters: Optional[Dict[str, str]] = None,
        table_type: Optional[TableInfo.TableType] = None,
        layout: Optional[Layout] = None,
        version: Optional[int] = None,
        previous_version: Optional[int] = None,
        version_creation_time: Optional[int] = None,
    ):
        """
        Constructor for TableBuilder.

        :param table_name: name of the table
        :param db_name: database name the table belongs to
        :param owner: owner of the table
        :param schema: schema containing column definitions
        :param partition_cols: partition columns
        :param parameters: table properties/parameters
        :param table_type: table type (NATIVE or IMPORTED)
        :param layout: layout information
        :param version: table version
        :param previous_version: previous version number
        :param version_creation_time: timestamp when version was created
        """
        self.table_name = table_name
        self.db_name = db_name
        self.owner = owner
        self.schema = schema
        self.partition_cols = partition_cols if partition_cols is not None else []
        self.parameters = parameters if parameters is not None else {}
        self.table_type = table_type
        self.layout = layout
        self.version = version
        self.previous_version = previous_version
        self.version_creation_time = version_creation_time

    def build(self) -> TableInfo:
        """
        Build and return the gRPC TableInfo object.

        :return: TableInfo protobuf message
        """
        table_info = TableInfo()
        table_info.table_name = self.table_name
        table_info.db_name = self.db_name
        
        if self.owner is not None:
            table_info.owner = self.owner
        
        if self.schema is not None:
            table_info.schema.CopyFrom(self.schema)
        
        if self.partition_cols:
            table_info.partition_cols.extend(self.partition_cols)
        
        table_info.parameters.update(self.parameters)
        
        if self.table_type is not None:
            table_info.type = self.table_type
        
        if self.layout is not None:
            table_info.layout.CopyFrom(self.layout)
        
        if self.version is not None:
            table_info.version = self.version
        
        if self.previous_version is not None:
            table_info.previous_version = self.previous_version
        
        if self.version_creation_time is not None:
            table_info.version_creation_time = self.version_creation_time
        
        return table_info
