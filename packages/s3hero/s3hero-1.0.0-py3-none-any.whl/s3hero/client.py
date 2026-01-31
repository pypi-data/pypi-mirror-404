"""
S3 Client Module - Core functionality for S3 operations.

Supports AWS S3, Cloudflare R2, and other S3-compatible services.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, BinaryIO, Callable, Dict, Iterator, List, Optional, Tuple
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError, NoCredentialsError


class S3Provider(Enum):
    """Supported S3 providers."""
    AWS = "aws"
    CLOUDFLARE_R2 = "cloudflare_r2"
    OTHER = "other"


@dataclass
class S3Config:
    """Configuration for S3 client connection."""
    provider: S3Provider
    access_key: str
    secret_key: str
    region: str = "us-east-1"
    endpoint_url: Optional[str] = None
    account_id: Optional[str] = None  # For Cloudflare R2

    def get_endpoint_url(self) -> Optional[str]:
        """Get the endpoint URL based on provider."""
        if self.endpoint_url:
            return self.endpoint_url
        
        if self.provider == S3Provider.CLOUDFLARE_R2:
            if not self.account_id:
                raise ValueError("Cloudflare R2 requires account_id")
            return f"https://{self.account_id}.r2.cloudflarestorage.com"
        
        return None  # AWS uses default endpoint


@dataclass
class S3Object:
    """Represents an S3 object."""
    key: str
    size: int
    last_modified: Any
    etag: Optional[str] = None
    storage_class: Optional[str] = None


@dataclass
class S3Bucket:
    """Represents an S3 bucket."""
    name: str
    creation_date: Any


class S3Client:
    """
    S3 Client for managing S3 operations.
    
    Supports AWS S3, Cloudflare R2, and other S3-compatible services.
    """

    def __init__(self, config: S3Config):
        """Initialize S3 client with configuration."""
        self.config = config
        self._client = self._create_client()

    def _create_client(self) -> Any:
        """Create boto3 S3 client."""
        client_config = Config(
            signature_version='s3v4',
            retries={'max_attempts': 3, 'mode': 'adaptive'}
        )

        endpoint_url = self.config.get_endpoint_url()

        return boto3.client(
            's3',
            aws_access_key_id=self.config.access_key,
            aws_secret_access_key=self.config.secret_key,
            region_name=self.config.region,
            endpoint_url=endpoint_url,
            config=client_config
        )

    # =====================
    # Bucket Operations
    # =====================

    def list_buckets(self) -> List[S3Bucket]:
        """List all buckets."""
        try:
            response = self._client.list_buckets()
            return [
                S3Bucket(
                    name=bucket['Name'],
                    creation_date=bucket['CreationDate']
                )
                for bucket in response.get('Buckets', [])
            ]
        except ClientError as e:
            raise S3Error(f"Failed to list buckets: {e}")

    def create_bucket(self, bucket_name: str, region: Optional[str] = None) -> bool:
        """Create a new bucket."""
        try:
            region = region or self.config.region
            
            # Handle region-specific bucket creation
            if region == 'us-east-1':
                self._client.create_bucket(Bucket=bucket_name)
            else:
                self._client.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': region}
                )
            return True
        except ClientError as e:
            raise S3Error(f"Failed to create bucket '{bucket_name}': {e}")

    def delete_bucket(self, bucket_name: str, force: bool = False) -> bool:
        """
        Delete a bucket.
        
        If force=True, empty the bucket first.
        """
        try:
            if force:
                self.empty_bucket(bucket_name)
            
            self._client.delete_bucket(Bucket=bucket_name)
            return True
        except ClientError as e:
            raise S3Error(f"Failed to delete bucket '{bucket_name}': {e}")

    def bucket_exists(self, bucket_name: str) -> bool:
        """Check if a bucket exists."""
        try:
            self._client.head_bucket(Bucket=bucket_name)
            return True
        except ClientError:
            return False

    def get_bucket_size(self, bucket_name: str) -> Tuple[int, int]:
        """Get bucket size (total bytes, object count)."""
        total_size = 0
        object_count = 0
        
        for obj in self.list_objects_iter(bucket_name):
            total_size += obj.size
            object_count += 1
        
        return total_size, object_count

    def empty_bucket(
        self,
        bucket_name: str,
        prefix: str = "",
        callback: Optional[Callable[[int], None]] = None
    ) -> int:
        """
        Empty a bucket (delete all objects).
        
        Returns the number of deleted objects.
        """
        deleted_count = 0
        objects_to_delete: List[Dict[str, str]] = []
        
        for obj in self.list_objects_iter(bucket_name, prefix):
            objects_to_delete.append({'Key': obj.key})
            
            # Delete in batches of 1000 (S3 limit)
            if len(objects_to_delete) >= 1000:
                self._delete_objects_batch(bucket_name, objects_to_delete)
                deleted_count += len(objects_to_delete)
                if callback:
                    callback(len(objects_to_delete))
                objects_to_delete = []
        
        # Delete remaining objects
        if objects_to_delete:
            self._delete_objects_batch(bucket_name, objects_to_delete)
            deleted_count += len(objects_to_delete)
            if callback:
                callback(len(objects_to_delete))
        
        # Also delete all versions if versioning is enabled
        try:
            deleted_count += self._delete_all_versions(bucket_name, callback)
        except ClientError:
            pass  # Versioning might not be enabled
        
        return deleted_count

    def _delete_objects_batch(
        self,
        bucket_name: str,
        objects: List[Dict[str, str]]
    ) -> None:
        """Delete a batch of objects."""
        if not objects:
            return
        
        try:
            self._client.delete_objects(
                Bucket=bucket_name,
                Delete={'Objects': objects, 'Quiet': True}
            )
        except ClientError as e:
            raise S3Error(f"Failed to delete objects: {e}")

    def _delete_all_versions(
        self,
        bucket_name: str,
        callback: Optional[Callable[[int], None]] = None
    ) -> int:
        """Delete all object versions (for versioned buckets)."""
        deleted_count = 0
        paginator = self._client.get_paginator('list_object_versions')
        
        for page in paginator.paginate(Bucket=bucket_name):
            objects_to_delete = []
            
            # Handle versions
            for version in page.get('Versions', []):
                objects_to_delete.append({
                    'Key': version['Key'],
                    'VersionId': version['VersionId']
                })
            
            # Handle delete markers
            for marker in page.get('DeleteMarkers', []):
                objects_to_delete.append({
                    'Key': marker['Key'],
                    'VersionId': marker['VersionId']
                })
            
            if objects_to_delete:
                self._client.delete_objects(
                    Bucket=bucket_name,
                    Delete={'Objects': objects_to_delete, 'Quiet': True}
                )
                deleted_count += len(objects_to_delete)
                if callback:
                    callback(len(objects_to_delete))
        
        return deleted_count

    # =====================
    # Object Operations
    # =====================

    def list_objects(
        self,
        bucket_name: str,
        prefix: str = "",
        max_keys: int = 1000
    ) -> List[S3Object]:
        """List objects in a bucket."""
        return list(self.list_objects_iter(bucket_name, prefix, max_keys))

    def list_objects_iter(
        self,
        bucket_name: str,
        prefix: str = "",
        max_keys: Optional[int] = None
    ) -> Iterator[S3Object]:
        """Iterate over objects in a bucket."""
        try:
            paginator = self._client.get_paginator('list_objects_v2')
            
            page_config = {'Bucket': bucket_name}
            if prefix:
                page_config['Prefix'] = prefix
            
            count = 0
            for page in paginator.paginate(**page_config):
                for obj in page.get('Contents', []):
                    if max_keys and count >= max_keys:
                        return
                    
                    yield S3Object(
                        key=obj['Key'],
                        size=obj['Size'],
                        last_modified=obj['LastModified'],
                        etag=obj.get('ETag'),
                        storage_class=obj.get('StorageClass')
                    )
                    count += 1
        except ClientError as e:
            raise S3Error(f"Failed to list objects: {e}")

    def upload_file(
        self,
        bucket_name: str,
        local_path: str,
        key: str,
        callback: Optional[Callable[[int], None]] = None,
        extra_args: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Upload a file to S3."""
        try:
            self._client.upload_file(
                local_path,
                bucket_name,
                key,
                Callback=callback,
                ExtraArgs=extra_args
            )
            return True
        except ClientError as e:
            raise S3Error(f"Failed to upload file: {e}")
        except FileNotFoundError:
            raise S3Error(f"Local file not found: {local_path}")

    def upload_fileobj(
        self,
        bucket_name: str,
        fileobj: BinaryIO,
        key: str,
        callback: Optional[Callable[[int], None]] = None,
        extra_args: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Upload a file object to S3."""
        try:
            self._client.upload_fileobj(
                fileobj,
                bucket_name,
                key,
                Callback=callback,
                ExtraArgs=extra_args
            )
            return True
        except ClientError as e:
            raise S3Error(f"Failed to upload file object: {e}")

    def download_file(
        self,
        bucket_name: str,
        key: str,
        local_path: str,
        callback: Optional[Callable[[int], None]] = None
    ) -> bool:
        """Download a file from S3."""
        try:
            self._client.download_file(
                bucket_name,
                key,
                local_path,
                Callback=callback
            )
            return True
        except ClientError as e:
            raise S3Error(f"Failed to download file: {e}")

    def delete_object(self, bucket_name: str, key: str) -> bool:
        """Delete an object from S3."""
        try:
            self._client.delete_object(Bucket=bucket_name, Key=key)
            return True
        except ClientError as e:
            raise S3Error(f"Failed to delete object: {e}")

    def delete_objects(
        self,
        bucket_name: str,
        keys: List[str],
        callback: Optional[Callable[[int], None]] = None
    ) -> int:
        """Delete multiple objects from S3."""
        deleted_count = 0
        
        # Delete in batches of 1000
        for i in range(0, len(keys), 1000):
            batch = keys[i:i + 1000]
            objects = [{'Key': key} for key in batch]
            
            try:
                response = self._client.delete_objects(
                    Bucket=bucket_name,
                    Delete={'Objects': objects, 'Quiet': False}
                )
                deleted_count += len(response.get('Deleted', []))
                if callback:
                    callback(len(batch))
            except ClientError as e:
                raise S3Error(f"Failed to delete objects: {e}")
        
        return deleted_count

    def copy_object(
        self,
        source_bucket: str,
        source_key: str,
        dest_bucket: str,
        dest_key: str
    ) -> bool:
        """Copy an object within or between buckets."""
        try:
            copy_source = {'Bucket': source_bucket, 'Key': source_key}
            self._client.copy_object(
                CopySource=copy_source,
                Bucket=dest_bucket,
                Key=dest_key
            )
            return True
        except ClientError as e:
            raise S3Error(f"Failed to copy object: {e}")

    def move_object(
        self,
        source_bucket: str,
        source_key: str,
        dest_bucket: str,
        dest_key: str
    ) -> bool:
        """Move an object within or between buckets."""
        self.copy_object(source_bucket, source_key, dest_bucket, dest_key)
        self.delete_object(source_bucket, source_key)
        return True

    def get_object_info(self, bucket_name: str, key: str) -> S3Object:
        """Get detailed information about an object."""
        try:
            response = self._client.head_object(Bucket=bucket_name, Key=key)
            return S3Object(
                key=key,
                size=response['ContentLength'],
                last_modified=response['LastModified'],
                etag=response.get('ETag'),
                storage_class=response.get('StorageClass')
            )
        except ClientError as e:
            raise S3Error(f"Failed to get object info: {e}")

    def object_exists(self, bucket_name: str, key: str) -> bool:
        """Check if an object exists."""
        try:
            self._client.head_object(Bucket=bucket_name, Key=key)
            return True
        except ClientError:
            return False

    def generate_presigned_url(
        self,
        bucket_name: str,
        key: str,
        expiration: int = 3600,
        http_method: str = 'get_object'
    ) -> str:
        """Generate a presigned URL for an object."""
        try:
            url = self._client.generate_presigned_url(
                http_method,
                Params={'Bucket': bucket_name, 'Key': key},
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            raise S3Error(f"Failed to generate presigned URL: {e}")

    # =====================
    # Sync Operations
    # =====================

    def sync_to_s3(
        self,
        local_dir: str,
        bucket_name: str,
        prefix: str = "",
        delete: bool = False,
        callback: Optional[Callable[[str, int], None]] = None
    ) -> Tuple[int, int, int]:
        """
        Sync local directory to S3.
        
        Returns (uploaded, skipped, deleted) counts.
        """
        import os
        
        uploaded = 0
        skipped = 0
        deleted = 0
        
        # Get existing S3 objects
        s3_objects = {obj.key: obj for obj in self.list_objects_iter(bucket_name, prefix)}
        local_keys = set()
        
        # Walk local directory
        for root, dirs, files in os.walk(local_dir):
            for filename in files:
                local_path = os.path.join(root, filename)
                relative_path = os.path.relpath(local_path, local_dir)
                s3_key = os.path.join(prefix, relative_path).replace('\\', '/')
                
                if s3_key.startswith('/'):
                    s3_key = s3_key[1:]
                
                local_keys.add(s3_key)
                
                # Check if file needs to be uploaded
                local_size = os.path.getsize(local_path)
                
                if s3_key in s3_objects and s3_objects[s3_key].size == local_size:
                    skipped += 1
                    continue
                
                self.upload_file(bucket_name, local_path, s3_key)
                uploaded += 1
                
                if callback:
                    callback(s3_key, local_size)
        
        # Delete extra files in S3
        if delete:
            for s3_key in s3_objects:
                if s3_key not in local_keys:
                    self.delete_object(bucket_name, s3_key)
                    deleted += 1
        
        return uploaded, skipped, deleted

    def sync_from_s3(
        self,
        bucket_name: str,
        local_dir: str,
        prefix: str = "",
        delete: bool = False,
        callback: Optional[Callable[[str, int], None]] = None
    ) -> Tuple[int, int, int]:
        """
        Sync S3 bucket to local directory.
        
        Returns (downloaded, skipped, deleted) counts.
        """
        import os
        
        downloaded = 0
        skipped = 0
        deleted = 0
        
        s3_keys = set()
        
        for obj in self.list_objects_iter(bucket_name, prefix):
            s3_keys.add(obj.key)
            
            # Calculate local path
            relative_key = obj.key
            if prefix and relative_key.startswith(prefix):
                relative_key = relative_key[len(prefix):].lstrip('/')
            
            local_path = os.path.join(local_dir, relative_key)
            
            # Create directory if needed
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            # Check if file needs to be downloaded
            if os.path.exists(local_path):
                local_size = os.path.getsize(local_path)
                if local_size == obj.size:
                    skipped += 1
                    continue
            
            self.download_file(bucket_name, obj.key, local_path)
            downloaded += 1
            
            if callback:
                callback(obj.key, obj.size)
        
        # Delete extra local files
        if delete:
            for root, dirs, files in os.walk(local_dir):
                for filename in files:
                    local_path = os.path.join(root, filename)
                    relative_path = os.path.relpath(local_path, local_dir)
                    s3_key = os.path.join(prefix, relative_path).replace('\\', '/')
                    
                    if s3_key.startswith('/'):
                        s3_key = s3_key[1:]
                    
                    if s3_key not in s3_keys:
                        os.remove(local_path)
                        deleted += 1
        
        return downloaded, skipped, deleted


class S3Error(Exception):
    """Custom exception for S3 operations."""
    pass
