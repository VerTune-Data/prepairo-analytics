"""
S3 Image Uploader for Meta Ads Reports
Uploads PNG charts to S3 and returns public URLs for Slack
"""

import boto3
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class S3ChartUploader:
    """Upload chart images to S3 for Slack display"""
    
    def __init__(self, bucket_name: str = "prepairo-analytics-reports", region: str = "ap-south-1"):
        self.bucket_name = bucket_name
        self.region = region
        self.s3_client = boto3.client("s3", region_name=region)
        self.base_url = f"https://{bucket_name}.s3.{region}.amazonaws.com"
        
    def upload_chart(self, local_path: str, object_key: Optional[str] = None) -> Optional[str]:
        """
        Upload a chart image to S3 and return the public URL
        
        Args:
            local_path: Path to the local PNG file
            object_key: S3 object key (path). If None, auto-generated from filename
            
        Returns:
            Public URL of the uploaded image, or None if upload fails
        """
        try:
            if not Path(local_path).exists():
                logger.error(f"Local file not found: {local_path}")
                return None
            
            # Generate object key if not provided
            if not object_key:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = Path(local_path).name
                object_key = f"meta-ads-charts/{timestamp}_{filename}"
            
            # Upload to S3 with public-read ACL
            logger.info(f"Uploading {local_path} to s3://{self.bucket_name}/{object_key}")
            
            self.s3_client.upload_file(
                local_path,
                self.bucket_name,
                object_key,
                ExtraArgs={
                    "ContentType": "image/png",
                    "CacheControl": "max-age=86400"  # 24 hours
                }
            )
            
            # Generate public URL
            public_url = f"{self.base_url}/{object_key}"
            logger.info(f"Chart uploaded successfully: {public_url}")
            
            return public_url
            
        except Exception as e:
            logger.error(f"Error uploading chart to S3: {e}", exc_info=True)
            return None
    
    def ensure_bucket_exists(self) -> bool:
        """Create bucket if it doesn't exist"""
        try:
            # Check if bucket exists
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"S3 bucket {self.bucket_name} exists")
            return True
            
        except:
            # Bucket doesn't exist, create it
            try:
                logger.info(f"Creating S3 bucket {self.bucket_name}")
                
                if self.region == "us-east-1":
                    self.s3_client.create_bucket(Bucket=self.bucket_name)
                else:
                    self.s3_client.create_bucket(
                        Bucket=self.bucket_name,
                        CreateBucketConfiguration={"LocationConstraint": self.region}
                    )
                
                # Set bucket policy for public read of charts folder
                bucket_policy = {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Sid": "PublicReadGetObject",
                            "Effect": "Allow",
                            "Principal": "*",
                            "Action": "s3:GetObject",
                            "Resource": f"arn:aws:s3:::{self.bucket_name}/meta-ads-charts/*"
                        }
                    ]
                }
                
                import json
                self.s3_client.put_bucket_policy(
                    Bucket=self.bucket_name,
                    Policy=json.dumps(bucket_policy)
                )
                
                logger.info(f"Bucket {self.bucket_name} created successfully")
                return True
                
            except Exception as e:
                logger.error(f"Error creating bucket: {e}")
                return False
