from dq_db_manager.handlers.maria.db_handler import MariaDBHandler

class MySQLDBHandler(MariaDBHandler):
    def __init__(self, connection_details):
        super().__init__(connection_details)