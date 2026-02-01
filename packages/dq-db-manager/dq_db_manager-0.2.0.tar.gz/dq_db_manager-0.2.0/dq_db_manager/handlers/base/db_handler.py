from abc import ABC, abstractmethod
from .connection_handler import BaseConnectionHandler
from .metadata_extractor import BaseMetadataExtractor

class BaseDBHandler(ABC):
    def __init__(self, connection_details):
        self.connection_handler = BaseConnectionHandler(connection_details)
        self.metadata_extractor = BaseMetadataExtractor(self.connection_handler.connection)

    def connect(self):
        return self.connection_handler.connect()

    def disconnect(self):
        self.connection_handler.disconnect()

    def test_connection(self):
        return self.connection_handler.test_connection()

    def extract_metadata(self):
        return self.metadata_extractor.extract_metadata()
