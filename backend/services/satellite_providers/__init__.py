"""
Satellite Provider Implementations
==================================

Each provider is in its own file with just 2 methods: connect() and download_image()
"""

from .base_strategy import SatelliteStrategy
from .sentinel_hub import SentinelHubStrategy
from .maxar import MaxarStrategy
from .airbus import AirbusStrategy
from .planet import PlanetStrategy

__all__ = [
    'SatelliteStrategy',
    'SentinelHubStrategy', 
    'MaxarStrategy',
    'AirbusStrategy',
    'PlanetStrategy'
]