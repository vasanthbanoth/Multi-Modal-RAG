import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from backend.app.core.config import settings, Settings
import io
import logging

class StorageService:
    """
    A simple wrapper for cloud storage (AWS S3) to upload and download files.
    """
    def __init__(self, config: Settings):
        """
        Initializes the S3 client. The service will be disabled if credentials
        are not fully provided.
        """
        self.bucket_name = config.S3_BUCKET_NAME
        self.s3_client = None
        self.is_enabled = False

        if all([config.AWS_ACCESS_KEY_ID, config.AWS_SECRET_ACCESS_KEY, config.AWS_REGION, config.S3_BUCKET_NAME]):
            logging.info("StorageService: AWS credentials found. Initializing S3 client.")
            try:
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=config.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
                    region_name=config.AWS_REGION
                )
                self.is_enabled = True
                logging.info("StorageService: S3 client initialized successfully.")
            except NoCredentialsError:
                logging.error("StorageService: AWS credentials not available.")
            except ClientError as e:
                logging.error("StorageService: Error initializing S3 client: %s", e)
        else:
            logging.warning("StorageService: AWS credentials or bucket name not fully configured. Service will be disabled.")

    def upload_file(self, file_obj: io.BytesIO, object_name: str) -> bool:
        """
        Upload a file-like object to an S3 bucket.

        Args:
            file_obj: File-like object.
            object_name: S3 object name (path/filename).
        Returns:
            True if file was uploaded, else False.
        """
        if not self.is_enabled:
            logging.error("Cannot upload file: StorageService is not enabled.")
            return False
        
        try:
            file_obj.seek(0) # Ensure we're at the start of the file stream
            self.s3_client.upload_fileobj(file_obj, self.bucket_name, object_name)
            logging.info("Successfully uploaded %s to bucket %s.", object_name, self.bucket_name)
        except ClientError as e:
            logging.error("Failed to upload %s: %s", object_name, e)
            return False
        return True

    def download_file_as_stream(self, object_name: str) -> io.BytesIO | None:
        """
        Downloads a file from an S3 bucket into a memory stream.

        Args:
            object_name: S3 object name (path/filename).
        Returns:
            An io.BytesIO stream of the file content, or None if download fails.
        """
        if not self.is_enabled:
            logging.error("Cannot download file: StorageService is not enabled.")
            return None

        try:
            file_stream = io.BytesIO()
            self.s3_client.download_fileobj(self.bucket_name, object_name, file_stream)
            file_stream.seek(0) # Rewind stream to the beginning
            logging.info("Successfully downloaded %s from bucket %s.", object_name, self.bucket_name)
            return file_stream
        except ClientError as e:
            logging.error("Failed to download %s: %s", object_name, e)
            return None

# Create a single, reusable instance of the service
storage_service = StorageService(settings)