class ConnectionDetailsParser:
    def __init__(self, connection_details):
        self.connection_details = connection_details

    def parse(self):
        # Basic validation or transformation of connection details.
        # This can be extended for specific databases if needed.
        if all(key in self.connection_details for key in ['user', 'password', 'host', 'port', 'database']):
            return self.connection_details
        raise ValueError("Invalid connection details")
