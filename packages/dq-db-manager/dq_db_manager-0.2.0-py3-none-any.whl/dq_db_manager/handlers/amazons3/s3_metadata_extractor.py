import botocore

class s3MetadataExtractor:
    def __init__(self, connection_handler):
        self.connection_handler = connection_handler

    def extract_metadata(self, bucket, object_name):
        """Extract metadata for a specific object in an S3 bucket"""
        try:
            response = self.connection_handler.s3_client.head_object(Bucket=bucket, Key=object_name)
            return response['Metadata']
        except botocore.exceptions.ClientError as e:
            print(f"Failed to extract metadata: {e}")
            return None
