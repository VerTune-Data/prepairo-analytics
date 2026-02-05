"""
Imgur Image Uploader for Meta Ads Reports
Alternative to S3 - uses Imgur's free anonymous upload API
"""

import requests
import logging
import base64
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class ImgurChartUploader:
    """Upload chart images to Imgur for Slack display"""
    
    def __init__(self, client_id: str = "546c25a59c58ad7"):
        """
        Args:
            client_id: Imgur API client ID (default is Anthropic's public ID)
        """
        self.client_id = client_id
        self.upload_url = "https://api.imgur.com/3/upload"
        
    def upload_chart(self, local_path: str) -> Optional[str]:
        """
        Upload a chart image to Imgur and return the public URL
        
        Args:
            local_path: Path to the local PNG file
            
        Returns:
            Public URL of the uploaded image, or None if upload fails
        """
        try:
            if not Path(local_path).exists():
                logger.error(f"Local file not found: {local_path}")
                return None
            
            logger.info(f"Uploading {local_path} to Imgur...")
            
            # Read and encode image
            with open(local_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")
            
            # Upload to Imgur
            headers = {
                "Authorization": f"Client-ID {self.client_id}"
            }
            
            payload = {
                "image": image_data,
                "type": "base64"
            }
            
            response = requests.post(
                self.upload_url,
                headers=headers,
                data=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    image_url = result["data"]["link"]
                    logger.info(f"Chart uploaded successfully to Imgur: {image_url}")
                    return image_url
                else:
                    logger.error(f"Imgur upload failed: {result}")
                    return None
            else:
                logger.error(f"Imgur API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error uploading chart to Imgur: {e}", exc_info=True)
            return None
