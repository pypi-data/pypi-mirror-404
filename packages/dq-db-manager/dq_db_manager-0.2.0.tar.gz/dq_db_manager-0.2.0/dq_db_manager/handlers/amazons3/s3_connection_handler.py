import boto3
import botocore
from dq_db_manager.handlers.base.connection_handler import BaseConnectionHandler

from .s3_connection_details_parser import ConnectionDetailsParser

class s3ConnectionHandler(BaseConnectionHandler):
    def __init__(self, connection_details):
        super().__init__(connection_details)  # Call to the superclass constructor
        parser = ConnectionDetailsParser(connection_details)
        parsed_details = parser.parse()  # Validate and parse connection details
        self.connection_details = parsed_details  # Store validated and parsed details
        self.s3_client = None  # Placeholder for the actual S3 client

    def connect(self):
        """Establish a connection to S3."""
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=self.connection_details['access_key_id'],
            aws_secret_access_key=self.connection_details['secret_access_key'],
            region_name=self.connection_details.get('region')
        )

    def disconnect(self):
        """Disconnect is not applicable for S3, but we'll clear the client."""
        self.s3_client = None

    def test_connection(self):
        """Override the test_connection to suit S3."""
        if self.s3_client is None:
            self.connect()  # Ensure we're connected before testing
        try:
            self.s3_client.list_buckets()
            print("Connection to AWS S3 was successful.")
            return True
        except botocore.exceptions.ClientError as e:
            print(f"Connection failed: {e}")
            return False
