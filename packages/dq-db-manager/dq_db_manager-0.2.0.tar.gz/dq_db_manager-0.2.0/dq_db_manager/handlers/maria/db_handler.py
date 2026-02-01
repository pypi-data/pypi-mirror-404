from .connection_handler import MariaConnectionHandler
from .metadata_extractor import MariaMetadataExtractor
from dq_db_manager.models.postgres import MetadataModels
from dq_db_manager.handlers.base.db_handler import BaseDBHandler

class MariaDBHandler(BaseDBHandler):
    def __init__(self, connection_details):
        self.models = MetadataModels
        self.connection_handler : MariaConnectionHandler = MariaConnectionHandler(connection_details)
        self.metadata_extractor :  MariaMetadataExtractor = MariaMetadataExtractor(self.connection_handler, self.models)

