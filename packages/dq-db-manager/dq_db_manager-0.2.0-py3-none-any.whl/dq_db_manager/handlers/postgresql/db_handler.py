from .connection_handler import PostgreSQLConnectionHandler
from .metadata_extractor import PostgreSQLMetadataExtractor
from dq_db_manager.models.postgres import MetadataModels
from dq_db_manager.handlers.base.db_handler import BaseDBHandler

class PostgreSQLDBHandler(BaseDBHandler):
    def __init__(self, connection_details):
        self.models = MetadataModels
        self.connection_handler : PostgreSQLConnectionHandler = PostgreSQLConnectionHandler(connection_details)
        self.metadata_extractor :  PostgreSQLMetadataExtractor = PostgreSQLMetadataExtractor(self.connection_handler, self.models)

    # ... Delegate connection and metadata extraction methods to connection_handler and metadata_extractor ...
