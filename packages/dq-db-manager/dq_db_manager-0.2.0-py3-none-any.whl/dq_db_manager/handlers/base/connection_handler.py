from abc import ABC, abstractmethod

class BaseConnectionHandler(ABC):
    def __init__(self, connection_details):
        self.connection_details = connection_details
        self.connection = None

    @abstractmethod
    def connect(self):
        """Establish a database connection."""
        pass

    @abstractmethod
    def disconnect(self):
        """Close the database connection."""
        pass

    @abstractmethod
    def test_connection(self):
        """Test the database connection."""
        pass
