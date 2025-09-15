"""
Base Strategy Interface
======================

Simple interface that all satellite providers must implement.
Only 2 methods needed: connect() and download_image()
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from PIL import Image


class SatelliteStrategy(ABC):
    """Base strategy for satellite providers"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    @abstractmethod
    def connect(self) -> bool:
        """Connect/authenticate with the satellite provider"""
        pass
    
    @abstractmethod
    def download_image(self, bbox: list, date_from: str, date_to: str, 
                      width: int = 1024, height: int = 1024) -> Optional[Image.Image]:
        """Download satellite image"""
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Provider name for logging"""
        pass