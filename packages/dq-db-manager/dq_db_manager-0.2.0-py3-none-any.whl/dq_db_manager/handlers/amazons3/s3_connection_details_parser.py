class ConnectionDetailsParser:
    def __init__(self, connection_details):
        self.connection_details = connection_details

    def parse(self):
        # Checking for required fields
        required_fields = ['bucket_name', 'access_key_id', 'secret_access_key']
        for field in required_fields:
            if not self.connection_details.get(field):
                raise ValueError(f"Missing required connection detail: {field}")

        # 'region' is optional but should be checked if present
        if 'region' in self.connection_details and not self.connection_details.get('region'):
            raise ValueError("Region specified but is invalid")

        return self.connection_details
