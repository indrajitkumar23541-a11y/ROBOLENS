import logging
from typing import Optional, Dict, Any
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from app.core.config import settings

logger = logging.getLogger(__name__)


class S3Service:
    def __init__(self):
        self.endpoint_url = settings.S3_ENDPOINT_URL
        self.public_endpoint_url = settings.S3_PUBLIC_ENDPOINT_URL or settings.S3_ENDPOINT_URL
        self.access_key = settings.S3_ACCESS_KEY
        self.secret_key = settings.S3_SECRET_KEY
        self.region = settings.S3_REGION
        self.bucket_raw = settings.S3_BUCKET_RAW
        self.bucket_processed = settings.S3_BUCKET_PROCESSED
        self.bucket_datasets = settings.S3_BUCKET_DATASETS

        boto_config = Config(
            signature_version="s3v4",
            connect_timeout=2,
            read_timeout=2,
            retries={"max_attempts": 2, "mode": "standard"},
            s3={"addressing_style": "path"}
        )

        self.client = boto3.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region,
            config=boto_config
        )

    def generate_presigned_upload_url(
        self,
        bucket: str,
        key: str,
        expires_in: int = 3600,
        content_type: str = "video/mp4"
    ) -> str:
        """
        Generate short-lived presigned PUT URL allowing mobile app
        to upload video directly to object storage.
        """
        try:
            url = self.client.generate_presigned_url(
                ClientMethod="put_object",
                Params={
                    "Bucket": bucket,
                    "Key": key,
                    "ContentType": content_type
                },
                ExpiresIn=expires_in
            )
            # If public endpoint is configured differently from internal container endpoint,
            # swap internal host for public host
            if self.public_endpoint_url and self.endpoint_url and self.public_endpoint_url != self.endpoint_url:
                url = url.replace(self.endpoint_url, self.public_endpoint_url)
            return url
        except ClientError as e:
            logger.error(f"Failed to generate presigned upload URL: {e}")
            raise

    def verify_object_exists(self, bucket: str, key: str) -> Optional[Dict[str, Any]]:
        """
        Verify that uploaded video exists in S3 and retrieve its size and metadata.
        Returns None if object does not exist.
        """
        try:
            response = self.client.head_object(Bucket=bucket, Key=key)
            return {
                "exists": True,
                "content_length": response.get("ContentLength", 0),
                "etag": response.get("ETag", "").strip('"'),
                "content_type": response.get("ContentType", ""),
                "last_modified": response.get("LastModified")
            }
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code in ["404", "NoSuchKey", "NotFound"]:
                return None
            logger.error(f"S3 head_object error for {bucket}/{key}: {e}")
            raise

    def generate_presigned_download_url(
        self,
        bucket: str,
        key: str,
        expires_in: int = 3600
    ) -> str:
        """Generate short-lived presigned GET URL for authorized downloads."""
        try:
            url = self.client.generate_presigned_url(
                ClientMethod="get_object",
                Params={"Bucket": bucket, "Key": key},
                ExpiresIn=expires_in
            )
            if self.public_endpoint_url and self.endpoint_url and self.public_endpoint_url != self.endpoint_url:
                url = url.replace(self.endpoint_url, self.public_endpoint_url)
            return url
        except ClientError as e:
            logger.error(f"Failed to generate presigned download URL: {e}")
            raise


s3_service = S3Service()
