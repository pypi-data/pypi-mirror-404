from .connection_handler import OracleConnectionHandler
from .metadata_extractor import OracleMetadataExtractor
from dq_db_manager.handlers.base.db_handler import BaseDBHandler
from dq_db_manager.models.postgres import MetadataModels

class OracleDBHandler(BaseDBHandler):
    def __init__(self, connection_details):
        self.models = MetadataModels
        self.connection_handler : OracleConnectionHandler = OracleConnectionHandler(connection_details)
        self.metadata_extractor :  OracleMetadataExtractor = OracleMetadataExtractor(self.connection_handler, self.models)

    # ... Delegate connection and metadata extraction methods to connection_handler and metadata_extractor ...
