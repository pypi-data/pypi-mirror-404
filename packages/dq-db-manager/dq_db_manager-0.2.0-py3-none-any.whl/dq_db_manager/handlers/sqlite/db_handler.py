from .connection_handler import SQLiteConnectionHandler
from .metadata_extractor import SQLiteMetadataExtractor
from dq_db_manager.models.postgres import MetadataModels
from dq_db_manager.handlers.base.db_handler import BaseDBHandler

class SQLiteDBHandler(BaseDBHandler):
    def __init__(self, connection_details):
        self.models = MetadataModels
        self.connection_handler : SQLiteConnectionHandler = SQLiteConnectionHandler(connection_details)
        self.metadata_extractor : SQLiteMetadataExtractor = SQLiteMetadataExtractor(self.connection_handler, self.models)

    # ... Delegate connection and metadata extraction methods to connection_handler and metadata_extractor ...
