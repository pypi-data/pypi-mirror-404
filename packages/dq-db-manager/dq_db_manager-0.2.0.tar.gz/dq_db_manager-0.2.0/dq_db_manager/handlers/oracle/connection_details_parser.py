class ConnectionDetailsParser:
    def __init__(self, connection_details):
        self.connection_details = connection_details

    def parse(self):
        if all(key in self.connection_details for key in ['user', 'password', 'host', 'port', 'service_name']):
            return self.connection_details
        raise ValueError("Invalid connection details")
