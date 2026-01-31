"""FieldSchemaBuilder for GooseFS FieldSchema objects."""
from typing import Optional

from goosefs_metastore_client.builders.abstract_builder import AbstractBuilder
from grpc_files.table_master_pb2 import FieldSchema


class FieldSchemaBuilder(AbstractBuilder):
    """Builds gRPC FieldSchema object for GooseFS."""

    def __init__(
        self,
        name: str,
        field_type: str,
        field_id: Optional[int] = None,
        comment: Optional[str] = None,
    ):
        """
        Constructor for FieldSchemaBuilder.

        :param name: name of the field/column
        :param field_type: type of the field (e.g., "string", "int", "bigint")
        :param field_id: unique identifier for the field
        :param comment: comment describing the field
        """
        self.name = name
        self.field_type = field_type
        self.field_id = field_id
        self.comment = comment

    def build(self) -> FieldSchema:
        """
        Build and return the gRPC FieldSchema object.

        :return: FieldSchema protobuf message
        """
        field_schema = FieldSchema()
        field_schema.name = self.name
        field_schema.type = self.field_type
        
        if self.field_id is not None:
            field_schema.id = self.field_id
        
        if self.comment is not None:
            field_schema.comment = self.comment
        
        return field_schema
