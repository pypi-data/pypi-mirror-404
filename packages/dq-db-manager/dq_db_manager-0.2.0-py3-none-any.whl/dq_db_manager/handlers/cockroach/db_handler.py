from dq_db_manager.handlers.postgresql.db_handler import PostgreSQLDBHandler

class CockroachHandler(PostgreSQLDBHandler):
    def __init__(self, connection_details):
        super().__init__(connection_details)

    # ... Delegate connection and metadata extraction methods to connection_handler and metadata_extractor ...
