"""
Sentinel Hub Provider
====================

Your current working implementation - moved from the original SatelliteService.
This is the proven, working code.
"""

import logging
import requests
from typing import Optional
from PIL import Image
from io import BytesIO

from .base_strategy import SatelliteStrategy

logger = logging.getLogger(__name__)


class SentinelHubStrategy(SatelliteStrategy):
    """Sentinel Hub implementation - your current working provider"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.client_id = config.get('client_id')
        self.client_secret = config.get('client_secret')
        self.base_url = config.get('base_url', 'https://services.sentinel-hub.com')
        self.access_token = None
    
    @property
    def provider_name(self) -> str:
        return "Sentinel Hub"
    
    def connect(self) -> bool:
        """Get Sentinel Hub access token"""
        token_url = f"{self.base_url}/oauth/token"
        data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        
        try:
            response = requests.post(token_url, data=data, timeout=30)
            if response.status_code == 200:
                self.access_token = response.json()['access_token']
                logger.info(f"Successfully authenticated with {self.provider_name}")
                return True
            else:
                logger.error(f"Failed to authenticate with {self.provider_name}: {response.status_code}")
                return False
        except requests.RequestException as e:
            logger.error(f"Network error connecting to {self.provider_name}: {str(e)}")
            return False
    
    def download_image(self, bbox: list, date_from: str, date_to: str, 
                      width: int = 1024, height: int = 1024) -> Optional[Image.Image]:
        """Download satellite image from Sentinel Hub"""
        if not self.access_token:
            if not self.connect():
                return None
                
        evalscript = """
        //VERSION=3
        function setup() {
            return {
                input: [{
                    bands: ["B02", "B03", "B04"]
                }],
                output: {
                    bands: 3,
                    sampleType: "AUTO"
                }
            };
        }

        function evaluatePixel(sample) {
            return [2.5 * sample.B04, 2.5 * sample.B03, 2.5 * sample.B02];
        }
        """

        payload = {
            "input": {
                "bounds": {
                    "bbox": bbox,
                    "properties": {"crs": "http://www.opengis.net/def/crs/EPSG/0/4326"}
                },
                "data": [{
                    "type": "sentinel-2-l2a",
                    "dataFilter": {
                        "timeRange": {
                            "from": f"{date_from}T00:00:00Z",
                            "to": f"{date_to}T23:59:59Z"
                        },
                        "maxCloudCoverage": 20
                    }
                }]
            },
            "output": {
                "width": width,
                "height": height,
                "responses": [{
                    "identifier": "default",
                    "format": {
                        "type": "image/jpeg"
                    }
                }]
            },
            "evalscript": evalscript
        }
        
        url = f"{self.base_url}/api/v1/process"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            
            if response.status_code == 200:
                image = Image.open(BytesIO(response.content))
                logger.info(f"Downloaded image from {self.provider_name}")
                return image
            else:
                logger.error(f"Error downloading from {self.provider_name}: {response.status_code}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Network error downloading from {self.provider_name}: {str(e)}")
            return None