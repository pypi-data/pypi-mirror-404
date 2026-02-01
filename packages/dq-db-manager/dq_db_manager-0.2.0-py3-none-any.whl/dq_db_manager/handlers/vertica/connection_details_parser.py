class ConnectionDetailsParser:
    def __init__(self, connection_details):
        self.connection_details = connection_details

    def parse(self):
        # Basic validation or transformation of connection details.
        # This can be extended for specific databases if needed.
        for key, value in self.connection_details.items():
            if key.lower() == 'port' and isinstance(value, str) and value.isdigit():
                self.connection_details[key] = int(value)
        if all(key in self.connection_details for key in ['user', 'password', 'host', 'port']):
            return self.connection_details
        raise ValueError("Invalid connection details")
