"""DatabaseBuilder for GooseFS Database objects."""
from typing import Dict, Optional

from goosefs_metastore_client.builders.abstract_builder import AbstractBuilder
from grpc_files.table_master_pb2 import Database, PrincipalType


class DatabaseBuilder(AbstractBuilder):
    """Builds gRPC Database object for GooseFS."""

    def __init__(
        self,
        db_name: str,
        description: Optional[str] = None,
        location: Optional[str] = None,
        parameters: Optional[Dict[str, str]] = None,
        owner_name: Optional[str] = None,
        owner_type: Optional[PrincipalType] = None,
        comment: Optional[str] = None,
    ):
        """
        Constructor for DatabaseBuilder.

        :param db_name: name of the database
        :param description: description of the database
        :param location: location URI for the database
        :param parameters: properties associated with the database
        :param owner_name: owner name for the database
        :param owner_type: owner type for the database (USER or ROLE)
        :param comment: comment for the database
        """
        self.db_name = db_name
        self.description = description
        self.location = location
        self.parameters = parameters if parameters is not None else {}
        self.owner_name = owner_name
        self.owner_type = owner_type
        self.comment = comment

    def build(self) -> Database:
        """
        Build and return the gRPC Database object.

        :return: Database protobuf message
        """
        database = Database()
        database.db_name = self.db_name
        
        if self.description is not None:
            database.description = self.description
        
        if self.location is not None:
            database.location = self.location
        
        database.parameter.update(self.parameters)
        
        if self.owner_name is not None:
            database.owner_name = self.owner_name
        
        if self.owner_type is not None:
            database.owner_type = self.owner_type
        
        if self.comment is not None:
            database.comment = self.comment
        
        return database
