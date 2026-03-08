from config.s3 import S3Client


class BaseService:
    def __init__(self):
        self.s3_client = S3Client()
