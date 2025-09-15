"""
S3 Storage Service
==================

Handles all S3 operations with organized folder structure and lifecycle management.
Structure: raw/, normalized/, heatmaps/ with aoi_id/date prefixing.
"""

import boto3
import logging
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from botocore.exceptions import ClientError, NoCredentialsError
from io import BytesIO
from PIL import Image

from config import Config

logger = logging.getLogger(__name__)


class S3StorageService:
    """
    S3 storage service with organized folder structure and signed URLs
    """
    
    def __init__(self):
        """Initialize S3 client with environment credentials"""
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=getattr(Config, 'AWS_ACCESS_KEY_ID', None),
                aws_secret_access_key=getattr(Config, 'AWS_SECRET_ACCESS_KEY', None),
                region_name=getattr(Config, 'AWS_S3_REGION', 'us-east-1')
            )
            self.bucket_name = getattr(Config, 'AWS_S3_BUCKET', None)
            
            if not self.bucket_name:
                raise ValueError("AWS_S3_BUCKET not configured")
                
            # Test connection
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            self.enabled = True
            logger.info(f"S3 service initialized for bucket: {self.bucket_name}")
            
        except (NoCredentialsError, ValueError, ClientError) as e:
            self.enabled = False
            logger.warning(f"S3 not available: {str(e)}")
    
    def _generate_s3_key(self, file_type: str, aoi_id: str, filename: str, date_str: str = None) -> str:
        """
        Generate organized S3 key with folder structure
        Format: {file_type}/aoi_{aoi_id}/{date}/{filename}
        """
        if not date_str:
            date_str = datetime.now().strftime('%Y-%m-%d')
            
        return f"{file_type}/aoi_{aoi_id}/{date_str}/{filename}"
    
    def upload_image(self, image: Image.Image, file_type: str, aoi_id: str, 
                    filename: str, date_str: str = None, quality: int = 95) -> Optional[Dict]:
        """
        Upload PIL image to S3 with organized structure
        
        Args:
            image: PIL Image object
            file_type: 'raw', 'normalized', or 'heatmaps'  
            aoi_id: AOI identifier
            filename: Base filename
            date_str: Date string (YYYY-MM-DD)
            quality: JPEG quality for compression
            
        Returns:
            Dict with s3_key, bucket, size, etc. or None if failed
        """
        if not self.enabled:
            return None
            
        try:
            # Generate S3 key
            s3_key = self._generate_s3_key(file_type, aoi_id, filename, date_str)
            
            # Convert image to bytes
            img_buffer = BytesIO()
            
            if filename.lower().endswith('.png'):
                image.save(img_buffer, format='PNG', optimize=True)
                content_type = 'image/png'
            else:
                image.save(img_buffer, format='JPEG', quality=quality, optimize=True)
                content_type = 'image/jpeg'
                
            img_buffer.seek(0)
            
            # Set metadata (remove tagging to avoid permission issues)
            metadata = {
                'aoi_id': str(aoi_id),
                'file_type': file_type,
                'upload_timestamp': datetime.now().isoformat(),
                'original_filename': filename
            }
            
            # Upload to S3 (without tagging to avoid permission issues)
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=img_buffer.getvalue(),
                ContentType=content_type,
                Metadata=metadata,
                StorageClass='STANDARD_IA' if file_type == 'heatmaps' else 'STANDARD'
            )
            
            # Get object size
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            
            result = {
                's3_key': s3_key,
                'bucket': self.bucket_name,
                'size': response['ContentLength'],
                'content_type': content_type,
                'file_type': file_type,
                'upload_timestamp': datetime.now().isoformat(),
                'storage_class': response.get('StorageClass', 'STANDARD')
            }
            
            logger.info(f"Uploaded {file_type} image to S3: {s3_key} ({result['size']} bytes)")
            return result
            
        except ClientError as e:
            logger.error(f"Failed to upload to S3: {str(e)}")
            return None
    
    def generate_signed_url(self, s3_key: str, expiration: int = 3600) -> Optional[str]:
        """
        Generate signed URL with TTL (default 1 hour)
        
        Args:
            s3_key: S3 object key
            expiration: URL expiration in seconds
            
        Returns:
            Signed URL string or None if failed
        """
        if not self.enabled:
            return None
            
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=expiration
            )
            
            logger.debug(f"Generated signed URL for {s3_key} (expires in {expiration}s)")
            return url
            
        except ClientError as e:
            logger.error(f"Failed to generate signed URL: {str(e)}")
            return None
    
    def delete_object(self, s3_key: str) -> bool:
        """Delete object from S3"""
        if not self.enabled:
            return False
            
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            logger.info(f"Deleted S3 object: {s3_key}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to delete S3 object {s3_key}: {str(e)}")
            return False
    
    def setup_lifecycle_policies(self) -> bool:
        """
        Setup S3 lifecycle policies for automatic cleanup
        - raw/: 30 days → IA, 90 days → Glacier, 365 days → delete
        - normalized/: 90 days → IA, 365 days → delete  
        - heatmaps/: 365 days → delete
        """
        if not self.enabled:
            return False
            
        lifecycle_config = {
            'Rules': [
                {
                    'ID': 'RawImagesLifecycle',
                    'Status': 'Enabled',
                    'Filter': {'Prefix': 'raw/'},
                    'Transitions': [
                        {
                            'Days': 30,
                            'StorageClass': 'STANDARD_IA'
                        },
                        {
                            'Days': 90,
                            'StorageClass': 'GLACIER'
                        }
                    ],
                    'Expiration': {'Days': 365}
                },
                {
                    'ID': 'NormalizedImagesLifecycle', 
                    'Status': 'Enabled',
                    'Filter': {'Prefix': 'normalized/'},
                    'Transitions': [
                        {
                            'Days': 90,
                            'StorageClass': 'STANDARD_IA'
                        }
                    ],
                    'Expiration': {'Days': 365}
                },
                {
                    'ID': 'HeatmapsLifecycle',
                    'Status': 'Enabled', 
                    'Filter': {'Prefix': 'heatmaps/'},
                    'Expiration': {'Days': 365}
                }
            ]
        }
        
        try:
            self.s3_client.put_bucket_lifecycle_configuration(
                Bucket=self.bucket_name,
                LifecycleConfiguration=lifecycle_config
            )
            logger.info("S3 lifecycle policies configured successfully")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to setup lifecycle policies: {str(e)}")
            return False
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics by folder"""
        if not self.enabled:
            return {}
            
        stats = {
            'raw': {'count': 0, 'size': 0},
            'normalized': {'count': 0, 'size': 0}, 
            'heatmaps': {'count': 0, 'size': 0},
            'total': {'count': 0, 'size': 0}
        }
        
        try:
            paginator = self.s3_client.get_paginator('list_objects_v2')
            
            for folder in ['raw', 'normalized', 'heatmaps']:
                pages = paginator.paginate(Bucket=self.bucket_name, Prefix=f"{folder}/")
                
                for page in pages:
                    if 'Contents' in page:
                        for obj in page['Contents']:
                            stats[folder]['count'] += 1
                            stats[folder]['size'] += obj['Size']
                            stats['total']['count'] += 1
                            stats['total']['size'] += obj['Size']
            
            return stats
            
        except ClientError as e:
            logger.error(f"Failed to get storage stats: {str(e)}")
            return {}


# Global S3 service instance
s3_service = S3StorageService()