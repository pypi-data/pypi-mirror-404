from abc import ABC, abstractmethod

class BaseMetadataExtractor(ABC):
    def __init__(self, connection):
        self.connection = connection


    # ... other metadata extraction methods ...
