# dq_db_manager/handlers/s3/s3_client_handler.py
import boto3
from .s3_connection_handler import s3ConnectionHandler
from .s3_metadata_extractor import s3MetadataExtractor
from dq_db_manager.handlers.base.db_handler import BaseDBHandler

class S3ClientHandler(BaseDBHandler):
    def __init__(self, connection_details):
        self.connection_handler : s3ConnectionHandler = s3ConnectionHandler(connection_details)
        self.metadata_extractor :  s3MetadataExtractor = s3MetadataExtractor(self.connection_handler)

