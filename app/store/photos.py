from __future__ import annotations

import boto3
from botocore.exceptions import ClientError

from app.config import Settings

PRESIGN_SECONDS = 300


class PhotoStore:
    def __init__(self, settings: Settings) -> None:
        self.bucket = settings.bucket_name
        self.region = settings.aws_region
        self.client = boto3.client("s3", **settings.aws_kwargs())  # type: ignore[call-overload]

    def create_if_missing(self) -> None:
        try:
            self.client.head_bucket(Bucket=self.bucket)
            return
        except ClientError as error:
            if error.response["Error"]["Code"] not in ("404", "NoSuchBucket"):
                raise
        options = {}
        if self.region != "us-east-1":
            options["CreateBucketConfiguration"] = {"LocationConstraint": self.region}
        self.client.create_bucket(Bucket=self.bucket, **options)
        self.client.put_public_access_block(
            Bucket=self.bucket,
            PublicAccessBlockConfiguration={
                "BlockPublicAcls": True,
                "IgnorePublicAcls": True,
                "BlockPublicPolicy": True,
                "RestrictPublicBuckets": True,
            },
        )
        self.client.put_bucket_encryption(
            Bucket=self.bucket,
            ServerSideEncryptionConfiguration={
                "Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]
            },
        )

    def put(self, key: str, data: bytes, metadata: dict[str, str]) -> None:
        self.client.put_object(
            Bucket=self.bucket, Key=key, Body=data, ContentType="image/jpeg", Metadata=metadata
        )

    def url(self, key: str) -> str:
        url: str = self.client.generate_presigned_url(
            "get_object", Params={"Bucket": self.bucket, "Key": key}, ExpiresIn=PRESIGN_SECONDS
        )
        return url
