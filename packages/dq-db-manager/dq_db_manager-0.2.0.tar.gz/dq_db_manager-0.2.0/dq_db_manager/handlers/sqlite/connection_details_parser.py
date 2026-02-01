class ConnectionDetailsParser:
    def __init__(self, connection_details):
        self.connection_details = connection_details

    def parse(self):
        # SQLite requires database file path
        # Optional parameters: timeout, check_same_thread, isolation_level, etc.
        if 'database' in self.connection_details:
            # Return the connection details as-is
            # SQLite accepts additional optional parameters that sqlite3.connect() supports
            return self.connection_details
        raise ValueError("Invalid connection details: 'database' (file path) is required for SQLite")
