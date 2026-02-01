import os
from typing import Optional
import boto3
from loguru import logger


class S3Client:

    def __init__(self, access_key: str, secret_key: str, endpoint: str, region: str, bucket: str, base_url: str):
        self.bucket = bucket
        self.base_url = base_url
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            endpoint_url=endpoint,
            region_name=region,
        )

    def upload_file(self, local_file_path, s3_file_name=None, ExtraArgs=None) -> Optional[str]:
        if not self.s3_client:
            logger.error("S3 客户端未初始化")
            raise ValueError("S3 客户端未初始化")

        if s3_file_name is None:
            s3_file_name = os.path.basename(local_file_path)
        try:
            self.s3_client.upload_file(
                local_file_path,
                self.bucket,
                s3_file_name,
                ExtraArgs=ExtraArgs,
            )
            file_url = f"{self.base_url}/{s3_file_name}"
            logger.info(f"文件已成功上传到 S3: {file_url}")
            return file_url
        except Exception as e:
            logger.error(f"上传文件到 S3 时出错: {e}")
            return None
