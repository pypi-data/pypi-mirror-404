from dq_db_manager.handlers.base.connection_handler import BaseConnectionHandler
from .connection_details_parser import ConnectionDetailsParser
import psycopg2

class PostgreSQLConnectionHandler(BaseConnectionHandler):
    def __init__(self, connection_details):
        parser = ConnectionDetailsParser(connection_details)
        parsed_details = parser.parse()
        self.connection = None
        super().__init__(parsed_details)

    def connect(self):
        try:
            self.connection = psycopg2.connect(**self.connection_details)
            return self.connection
        except psycopg2.Error as e:
            print(f"Error connecting to PostgreSQL: {e}")
            raise

    def disconnect(self):
        if self.connection:
            self.connection.close()

    def test_connection(self):
        try:
            
            self.connect()
            return True
        except psycopg2.Error as e:
            print(f"Error testing PostgreSQL connection: {e}")
            return False
        finally:
            self.disconnect()

    def execute_query(self, query, params=None):
        try:
            self.connect()
            cursor = self.connection.cursor()
            cursor.execute(query, params)

            # Get column names from cursor description
            columns = [desc[0] for desc in cursor.description] if cursor.description else []

            # Fetch all rows
            rows = cursor.fetchall()

            # Convert to list of dictionaries
            results = [dict(zip(columns, row)) for row in rows]

            cursor.close()
            return results
        except psycopg2.Error as e:
            print(f"Error executing PostgreSQL query: {e}")
            raise
        finally:
            self.disconnect()
