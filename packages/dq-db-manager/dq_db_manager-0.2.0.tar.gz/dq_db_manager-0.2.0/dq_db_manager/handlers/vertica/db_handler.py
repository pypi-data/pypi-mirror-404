from .connection_handler import VerticaConnectionHandler
from .metadata_extractor import VerticaMetadataExtractor
from dq_db_manager.handlers.base.db_handler import BaseDBHandler
from dq_db_manager.models.postgres import MetadataModels

class VerticaHandler(BaseDBHandler):
    def __init__(self, connection_details):
        self.models = MetadataModels
        self.connection_handler : VerticaConnectionHandler = VerticaConnectionHandler(connection_details)
        self.metadata_extractor :  VerticaMetadataExtractor = VerticaMetadataExtractor(self.connection_handler, self.models)