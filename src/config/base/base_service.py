from config.s3 import S3Client


class BaseService:
    def __init__(self):
        self._s3_client = None

    @property
    def s3_client(self):
        if self._s3_client is None:
            self._s3_client = S3Client()
        return self._s3_client
