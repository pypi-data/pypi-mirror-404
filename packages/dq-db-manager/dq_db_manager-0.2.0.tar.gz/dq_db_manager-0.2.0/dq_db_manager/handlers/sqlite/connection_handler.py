from dq_db_manager.handlers.base.connection_handler import BaseConnectionHandler
from .connection_details_parser import ConnectionDetailsParser
import sqlite3

class SQLiteConnectionHandler(BaseConnectionHandler):
    def __init__(self, connection_details):
        parser = ConnectionDetailsParser(connection_details)
        parsed_details = parser.parse()
        self.connection = None
        super().__init__(parsed_details)

    def connect(self):
        try:
            self.connection = sqlite3.connect(**self.connection_details)
            return self.connection
        except sqlite3.Error as e:
            print(f"Error connecting to SQLite: {e}")
            raise

    def disconnect(self):
        if self.connection:
            self.connection.close()

    def test_connection(self):
        try:
            self.connect()
            return True
        except sqlite3.Error as e:
            print(f"Error testing SQLite connection: {e}")
            return False
        finally:
            self.disconnect()

    def execute_query(self, query, params=None):
        try:
            self.connect()
            cursor = self.connection.cursor()

            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            # Get column names from cursor description
            columns = [desc[0] for desc in cursor.description] if cursor.description else []

            # Fetch all rows
            rows = cursor.fetchall()

            # Convert to list of dictionaries (following PostgreSQL pattern)
            results = [dict(zip(columns, row)) for row in rows]

            cursor.close()
            return results
        except sqlite3.Error as e:
            print(f"Error executing SQLite query: {e}")
            raise
        finally:
            self.disconnect()
