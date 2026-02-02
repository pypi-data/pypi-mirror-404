import aioboto3
from botocore.config import Config as BotoConfig


class StorageClient:
    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket: str,
    ):
        self.endpoint = endpoint
        self.access_key = access_key
        self.secret_key = secret_key
        self.bucket = bucket
        self._session = aioboto3.Session()

    def _get_client_config(self) -> dict:
        return {
            "service_name": "s3",
            "endpoint_url": self.endpoint,
            "aws_access_key_id": self.access_key,
            "aws_secret_access_key": self.secret_key,
            "config": BotoConfig(
                signature_version="s3v4",
                retries={"max_attempts": 3, "mode": "adaptive"},
            ),
        }

    async def upload(self, key: str, data: bytes) -> None:
        async with self._session.client(**self._get_client_config()) as s3:
            await s3.put_object(Bucket=self.bucket, Key=key, Body=data)

    async def download(self, key: str) -> bytes:
        async with self._session.client(**self._get_client_config()) as s3:
            response = await s3.get_object(Bucket=self.bucket, Key=key)
            return await response["Body"].read()

    async def exists(self, key: str) -> bool:
        async with self._session.client(**self._get_client_config()) as s3:
            try:
                await s3.head_object(Bucket=self.bucket, Key=key)
                return True
            except Exception:
                return False

    async def delete(self, key: str) -> None:
        async with self._session.client(**self._get_client_config()) as s3:
            await s3.delete_object(Bucket=self.bucket, Key=key)

    async def list_objects(self, prefix: str) -> list[str]:
        async with self._session.client(**self._get_client_config()) as s3:
            response = await s3.list_objects_v2(Bucket=self.bucket, Prefix=prefix)
            return [obj["Key"] for obj in response.get("Contents", [])]

    async def health_check(self) -> bool:
        try:
            async with self._session.client(**self._get_client_config()) as s3:
                await s3.head_bucket(Bucket=self.bucket)
                return True
        except Exception:
            return False
