"""
Satellite image processing service
Handles all satellite image download, processing, and analysis operations

Updated to use strategy pattern internally while maintaining the same interface.
"""
import os
import uuid
import logging
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from PIL import Image
from typing import Optional, Dict, Any

from config import Config
from services.satellite_providers import SentinelHubStrategy

logger = logging.getLogger(__name__)


class SatelliteService:
    """
    Service for satellite image operations
    
    Now uses strategy pattern internally but maintains the exact same interface
    for backward compatibility with existing code.
    """
    
    def __init__(self, client_id, client_secret):
        # Legacy attributes for backward compatibility
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.base_url = "https://services.sentinel-hub.com"  # Kept for backward compatibility
        
        # Initialize strategy internally
        self._strategy = SentinelHubStrategy({
            'client_id': client_id,
            'client_secret': client_secret
        })
        
    def get_access_token(self):
        """Get Sentinel Hub access token"""
        success = self._strategy.connect()
        if success and hasattr(self._strategy, 'access_token'):
            self.access_token = self._strategy.access_token
        return success
    
    def download_image(self, bbox, date_from, date_to, width=1024, height=1024):
        """Download satellite image from Sentinel Hub"""
        return self._strategy.download_image(bbox, date_from, date_to, width, height)
    
    def create_heatmap(self, image1, image2, filename):
        """Create change detection heatmap"""
        try:
            img1_array = np.array(image1)
            img2_array = np.array(image2)
            
            # Handle size mismatch by resizing to match
            if img1_array.shape != img2_array.shape:
                logger.info(f"Images have different sizes: {img1_array.shape} vs {img2_array.shape}")
                
                # Find target size (smaller of the two)
                target_height = min(img1_array.shape[0], img2_array.shape[0])
                target_width = min(img1_array.shape[1], img2_array.shape[1])
                
                # Resize both images to match
                img1_resized = Image.fromarray(img1_array).resize((target_width, target_height), Image.Resampling.LANCZOS)
                img2_resized = Image.fromarray(img2_array).resize((target_width, target_height), Image.Resampling.LANCZOS)
                
                img1_array = np.array(img1_resized)
                img2_array = np.array(img2_resized)
                
                logger.info(f"Resized images to: {img1_array.shape}")
            
            diff = np.abs(img1_array.astype(float) - img2_array.astype(float))
            
            if len(diff.shape) == 3:
                diff_gray = np.mean(diff, axis=2)
            else:
                diff_gray = diff
            
            # Create figure with same aspect ratio as the images
            height, width = diff_gray.shape
            aspect_ratio = width / height
            fig_size = 6  # Smaller size to match other images
            
            fig, ax = plt.subplots(1, 1, figsize=(fig_size, fig_size / aspect_ratio), dpi=100)
            
            threshold = np.percentile(diff_gray, 75)
            enhanced_diff = np.where(diff_gray > threshold, diff_gray, 0)
            
            im = ax.imshow(enhanced_diff, cmap='hot', interpolation='bilinear')
            
            ax.set_title('Change Detection Heatmap', fontsize=14, fontweight='bold', pad=10)
            ax.axis('off')
            
            cbar = plt.colorbar(im, ax=ax, shrink=0.8, aspect=20)
            cbar.set_label('Change Intensity', rotation=270, labelpad=15, fontsize=10)
            
            plt.tight_layout()
            plt.savefig(filename, dpi=150, bbox_inches='tight', facecolor='white', edgecolor='none')
            plt.close()
            
            logger.info(f"Created heatmap: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Error creating heatmap: {str(e)}")
            return None
    
    def calculate_change_percentage(self, image1, image2):
        """Calculate the change percentage between two images"""
        try:
            img1_array = np.array(image1)
            img2_array = np.array(image2)
            
            # Handle size mismatch
            if img1_array.shape != img2_array.shape:
                target_height = min(img1_array.shape[0], img2_array.shape[0])
                target_width = min(img1_array.shape[1], img2_array.shape[1])
                img1_resized = Image.fromarray(img1_array).resize((target_width, target_height), Image.Resampling.LANCZOS)
                img2_resized = Image.fromarray(img2_array).resize((target_width, target_height), Image.Resampling.LANCZOS)
                img1_array = np.array(img1_resized)
                img2_array = np.array(img2_resized)
            
            diff = np.abs(img1_array.astype(float) - img2_array.astype(float))
            change_percentage = (np.mean(diff) / 255.0) * 100
            return change_percentage
        except Exception as e:
            logger.error(f"Error calculating change percentage: {str(e)}")
            return 0.0
    
    def save_image(self, image, filename, quality=95):
        """Save image to disk"""
        try:
            filepath = os.path.join(Config.IMAGES_DIR, filename)
            image.save(filepath, 'JPEG', quality=quality)
            logger.info(f"Saved image: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Error saving image: {str(e)}")
            return None
    
    def load_baseline_image(self, baseline_filename):
        """Load baseline image from disk"""
        try:
            baseline_path = os.path.join(Config.IMAGES_DIR, baseline_filename)
            if not os.path.exists(baseline_path):
                logger.error(f"Baseline image not found: {baseline_path}")
                return None
            
            return Image.open(baseline_path)
        except Exception as e:
            logger.error(f"Error loading baseline image: {str(e)}")
            return None