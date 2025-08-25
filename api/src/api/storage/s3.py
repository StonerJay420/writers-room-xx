"""S3/DigitalOcean Spaces storage operations with CDN support."""
import boto3
import hashlib
import hmac
import time
from typing import Optional, BinaryIO, Union, Dict, Any
from pathlib import Path

from ..config import settings


class S3Storage:
    """S3/Spaces storage client with CDN support."""
    
    def __init__(self):
        """Initialize S3 client if credentials are configured."""
        self.client = None
        self.bucket = settings.s3_bucket
        self.cdn_domain = settings.s3_cdn_domain
        self.signing_secret = settings.s3_signing_secret
        
        if all([settings.s3_endpoint, settings.s3_access_key, settings.s3_secret_key]):
            self.client = boto3.client(
                's3',
                endpoint_url=settings.s3_endpoint,
                aws_access_key_id=settings.s3_access_key,
                aws_secret_access_key=settings.s3_secret_key
            )
    
    def generate_cdn_url(self, key: str, ttl_seconds: int = 3600) -> str:
        """Generate CDN URL with optional signed access."""
        if not self.cdn_domain:
            # Fallback to direct S3/Spaces URL
            if self.client and self.bucket:
                return f"{settings.s3_endpoint}/{self.bucket}/{key}"
            return f"/storage/{key}"  # Local fallback
        
        base_url = f"https://{self.cdn_domain}/{key}"
        
        if self.signing_secret:
            # Add signed URL parameters
            expiry = int(time.time()) + ttl_seconds
            signature_data = f"{key}{expiry}"
            signature = hmac.new(
                self.signing_secret.encode(),
                signature_data.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return f"{base_url}?exp={expiry}&sig={signature}"
        
        return base_url
    
    def put_object_with_cache(
        self,
        key: str,
        body: Union[bytes, BinaryIO],
        content_type: str,
        cache_control: str = "public, max-age=86400"
    ) -> bool:
        """Upload object with cache control headers."""
        if not self.client or not self.bucket:
            print(f"S3 storage not configured, would store {key} locally")
            return False
        
        try:
            extra_args = {
                'ContentType': content_type,
                'CacheControl': cache_control,
                'ACL': 'public-read'
            }
            
            if isinstance(body, bytes):
                self.client.put_object(
                    Bucket=self.bucket,
                    Key=key,
                    Body=body,
                    **extra_args
                )
            else:
                self.client.upload_fileobj(
                    body,
                    self.bucket,
                    key,
                    ExtraArgs=extra_args
                )
            
            return True
            
        except Exception as e:
            print(f"Error uploading to S3: {e}")
            return False
    
    def list_objects(self, prefix: str = "") -> list:
        """List objects in the bucket with a given prefix."""
        if not self.client or not self.bucket:
            return []
        
        try:
            response = self.client.list_objects_v2(
                Bucket=self.bucket,
                Prefix=prefix
            )
            
            objects = []
            for obj in response.get('Contents', []):
                objects.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'].isoformat(),
                    'cdn_url': self.generate_cdn_url(obj['Key'])
                })
            
            return objects
            
        except Exception as e:
            print(f"Error listing S3 objects: {e}")
            return []
    
    def delete_object(self, key: str) -> bool:
        """Delete an object from S3."""
        if not self.client or not self.bucket:
            return False
        
        try:
            self.client.delete_object(Bucket=self.bucket, Key=key)
            return True
        except Exception as e:
            print(f"Error deleting S3 object: {e}")
            return False


# Global storage instance
storage = S3Storage()