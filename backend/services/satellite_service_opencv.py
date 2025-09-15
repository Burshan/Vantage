"""
Enhanced Satellite Service with OpenCV
Improved performance and advanced change detection capabilities
"""
import os
import uuid
import logging
import numpy as np
import cv2
from datetime import datetime, timedelta
from PIL import Image
from typing import Optional, Dict, Any, Tuple

from config import Config
from services.satellite_providers import SentinelHubStrategy

# Try to import S3 service
try:
    from services.s3_service import s3_service
    S3_AVAILABLE = True
except ImportError:
    s3_service = None
    S3_AVAILABLE = False

logger = logging.getLogger(__name__)


class SatelliteServiceOpenCV:
    """
    Enhanced satellite service using OpenCV for superior performance
    and advanced image processing capabilities
    """
    
    def __init__(self, client_id, client_secret):
        # Legacy attributes for backward compatibility
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.base_url = "https://services.sentinel-hub.com"
        
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
    
    def _detect_cloud_coverage(self, image_array: np.ndarray) -> float:
        """
        Advanced cloud detection using multiple methods:
        1. Spectral analysis (brightness + low saturation)
        2. Texture analysis (smooth areas)
        3. Statistical thresholding
        """
        try:
            if len(image_array.shape) == 3:
                # RGB image - use full spectral analysis
                gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
                hsv = cv2.cvtColor(image_array, cv2.COLOR_RGB2HSV)
                
                # Method 1: Spectral-based detection
                brightness_mask = (gray > 200)  # Very bright pixels
                saturation_mask = (hsv[:,:,1] < 40)  # Low saturation (white/gray)
                spectral_clouds = brightness_mask & saturation_mask
                
                # Method 2: Texture-based detection (clouds are smooth)
                # Calculate local standard deviation
                kernel = np.ones((7,7), np.float32) / 49
                mean_filtered = cv2.filter2D(gray.astype(np.float32), -1, kernel)
                sqr_filtered = cv2.filter2D((gray.astype(np.float32))**2, -1, kernel)
                local_std = np.sqrt(np.abs(sqr_filtered - mean_filtered**2))
                
                texture_clouds = (local_std < 12) & (gray > 180)
                
                # Method 3: Blue/Red ratio analysis (clouds reflect blue more)
                if image_array.shape[2] >= 3:
                    blue_red_ratio = image_array[:,:,2].astype(float) / (image_array[:,:,0].astype(float) + 1)
                    ratio_clouds = (blue_red_ratio > 0.95) & (gray > 190)
                else:
                    ratio_clouds = np.zeros_like(gray, dtype=bool)
                
                # Combine all methods with weights
                combined_mask = (spectral_clouds.astype(float) * 0.4 + 
                               texture_clouds.astype(float) * 0.4 + 
                               ratio_clouds.astype(float) * 0.2)
                
                # Apply morphological operations to clean up noise
                kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5,5))
                combined_mask = cv2.morphologyEx((combined_mask > 0.5).astype(np.uint8), 
                                               cv2.MORPH_CLOSE, kernel)
                combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, kernel)
                
                cloud_coverage = (np.sum(combined_mask) / combined_mask.size) * 100
                
            else:
                # Grayscale image - simplified detection
                gray = image_array
                bright_pixels = np.sum(gray > 200)
                total_pixels = gray.size
                cloud_coverage = (bright_pixels / total_pixels) * 100
            
            return float(min(100.0, max(0.0, cloud_coverage)))
            
        except Exception as e:
            logger.error(f"Error in cloud detection: {str(e)}")
            # Fallback to simple brightness-based detection
            gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY) if len(image_array.shape) == 3 else image_array
            bright_pixels = np.sum(gray > 200)
            return float((bright_pixels / gray.size) * 100)
    
    def _apply_cloud_mask(self, image1_array: np.ndarray, image2_array: np.ndarray) -> tuple:
        """
        Apply cloud masking to both images for change detection
        Returns masked images where cloudy areas are excluded
        """
        try:
            # Detect clouds in both images
            cloud_mask1 = self._get_cloud_mask(image1_array)
            cloud_mask2 = self._get_cloud_mask(image2_array)
            
            # Combined mask: exclude pixels that are cloudy in either image
            combined_cloud_mask = cloud_mask1 | cloud_mask2
            
            # Create clean mask (True where analysis should be performed)
            clean_mask = ~combined_cloud_mask
            
            return clean_mask, combined_cloud_mask
            
        except Exception as e:
            logger.error(f"Error applying cloud mask: {str(e)}")
            # Return no masking if there's an error
            clean_mask = np.ones(image1_array.shape[:2], dtype=bool)
            cloud_mask = np.zeros(image1_array.shape[:2], dtype=bool)
            return clean_mask, cloud_mask
    
    def _get_cloud_mask(self, image_array: np.ndarray) -> np.ndarray:
        """Get binary cloud mask for an image"""
        try:
            if len(image_array.shape) == 3:
                gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
                hsv = cv2.cvtColor(image_array, cv2.COLOR_RGB2HSV)
                
                # Multi-criteria cloud detection
                brightness_mask = (gray > 200)
                saturation_mask = (hsv[:,:,1] < 40)
                cloud_mask = brightness_mask & saturation_mask
                
                # Clean up with morphological operations
                kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3,3))
                cloud_mask = cv2.morphologyEx(cloud_mask.astype(np.uint8), cv2.MORPH_CLOSE, kernel)
                
                return cloud_mask.astype(bool)
            else:
                # Grayscale
                return (image_array > 200)
                
        except Exception as e:
            logger.error(f"Error getting cloud mask: {str(e)}")
            return np.zeros(image_array.shape[:2], dtype=bool)

    def assess_image_quality(self, image: Image.Image) -> Dict[str, float]:
        """Assess image quality metrics"""
        try:
            # Convert PIL to OpenCV format
            img_array = np.array(image)
            if len(img_array.shape) == 3:
                # Convert RGB to BGR for OpenCV
                img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            else:
                gray = img_array
            
            # Calculate image quality metrics
            contrast = np.std(gray)
            brightness = np.mean(gray)
            sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # Advanced cloud coverage estimation
            estimated_cloud_coverage = self._detect_cloud_coverage(img_array)
            
            return {
                'contrast': float(contrast),
                'brightness': float(brightness),
                'sharpness': float(sharpness),
                'estimated_cloud_coverage': float(estimated_cloud_coverage),
                'quality_score': float(min(100, (sharpness / 500) * (contrast / 50) * 100))  # Normalized quality score
            }
        except Exception as e:
            logger.error(f"Error assessing image quality: {str(e)}")
            return {
                'contrast': 0.0,
                'brightness': 0.0,
                'sharpness': 0.0,
                'estimated_cloud_coverage': 100.0,
                'quality_score': 0.0
            }
    
    def create_heatmap_opencv(self, image1: Image.Image, image2: Image.Image, filename: str, aoi_id: int = None) -> Dict[str, Any]:
        """Create advanced change detection heatmap using OpenCV"""
        try:
            # Convert PIL images to OpenCV format
            img1_array = np.array(image1)
            img2_array = np.array(image2)
            
            # Handle size mismatch by resizing to match
            if img1_array.shape != img2_array.shape:
                logger.info(f"Images have different sizes: {img1_array.shape} vs {img2_array.shape}")
                target_height = min(img1_array.shape[0], img2_array.shape[0])
                target_width = min(img1_array.shape[1], img2_array.shape[1])
                
                img1_array = cv2.resize(img1_array, (target_width, target_height), interpolation=cv2.INTER_LANCZOS4)
                img2_array = cv2.resize(img2_array, (target_width, target_height), interpolation=cv2.INTER_LANCZOS4)
                
                logger.info(f"Resized images to: {img1_array.shape}")
            
            # Convert to grayscale for change detection
            if len(img1_array.shape) == 3:
                gray1 = cv2.cvtColor(img1_array, cv2.COLOR_RGB2GRAY)
                gray2 = cv2.cvtColor(img2_array, cv2.COLOR_RGB2GRAY)
            else:
                gray1 = img1_array
                gray2 = img2_array
            
            # Apply cloud masking
            clean_mask, cloud_mask = self._apply_cloud_mask(img1_array, img2_array)
            
            # Apply Gaussian blur to reduce noise
            gray1_blur = cv2.GaussianBlur(gray1, (5, 5), 0)
            gray2_blur = cv2.GaussianBlur(gray2, (5, 5), 0)
            
            # Calculate absolute difference
            diff = cv2.absdiff(gray1_blur, gray2_blur)
            
            # Mask out cloudy areas in the difference image
            diff_masked = diff.copy()
            diff_masked[cloud_mask] = 0  # Set cloudy areas to 0 (no change)
            
            # Apply morphological operations to reduce noise
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            diff_masked = cv2.morphologyEx(diff_masked, cv2.MORPH_CLOSE, kernel)
            
            # Enhance changes using adaptive threshold
            threshold = cv2.threshold(diff_masked, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[0]
            enhanced_diff = cv2.threshold(diff_masked, threshold * 0.7, 255, cv2.THRESH_BINARY)[1]
            
            # Apply custom colormap for better visualization
            colored_heatmap = self._apply_custom_colormap_with_mask(diff_masked, cloud_mask)
            
            # Save the heatmap locally
            cv2.imwrite(filename, colored_heatmap)
            logger.info(f"Created OpenCV heatmap: {filename}")
            
            result = {
                'local_path': filename,
                's3_key': None,
                'filename': os.path.basename(filename)
            }
            
            # Upload to S3 if available and enabled
            if S3_AVAILABLE and s3_service and s3_service.enabled and aoi_id:
                try:
                    # Convert OpenCV image back to PIL for S3 upload
                    pil_image = Image.fromarray(cv2.cvtColor(colored_heatmap, cv2.COLOR_BGR2RGB))
                    
                    # Upload to S3
                    s3_result = s3_service.upload_image(
                        image=pil_image,
                        file_type='heatmaps',
                        aoi_id=str(aoi_id),
                        filename=os.path.basename(filename)
                    )
                    
                    if s3_result:
                        result['s3_key'] = s3_result['s3_key']
                        logger.info(f"✅ Uploaded heatmap to S3: {s3_result['s3_key']}")
                    else:
                        logger.warning(f"❌ Failed to upload heatmap {filename} to S3")
                        
                except Exception as e:
                    logger.error(f"S3 upload error for heatmap {filename}: {str(e)}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error creating OpenCV heatmap: {str(e)}")
            return {'local_path': None, 's3_key': None, 'filename': filename}
    
    def _apply_custom_colormap(self, diff_image: np.ndarray) -> np.ndarray:
        """Apply custom colormap for change detection visualization"""
        # Normalize to 0-255 range
        normalized = cv2.normalize(diff_image, None, 0, 255, cv2.NORM_MINMAX)
        
        # Apply color mapping: blue (no change) -> yellow (moderate) -> red (high change)
        colored = cv2.applyColorMap(normalized, cv2.COLORMAP_HOT)
        
        # Enhance contrast
        colored = cv2.convertScaleAbs(colored, alpha=1.2, beta=10)
        
        return colored
    
    def _apply_custom_colormap_with_mask(self, diff_image: np.ndarray, cloud_mask: np.ndarray) -> np.ndarray:
        """Apply custom colormap with cloud masking visualization"""
        # Normalize difference image to 0-255 range
        normalized = cv2.normalize(diff_image, None, 0, 255, cv2.NORM_MINMAX)
        
        # Apply color mapping: blue (no change) -> yellow (moderate) -> red (high change)
        colored = cv2.applyColorMap(normalized, cv2.COLORMAP_HOT)
        
        # Enhance contrast
        colored = cv2.convertScaleAbs(colored, alpha=1.2, beta=10)
        
        # Overlay cloud mask in a distinct color (light gray/transparent)
        cloud_overlay = np.zeros_like(colored)
        cloud_overlay[cloud_mask] = [200, 200, 200]  # Light gray for clouds
        
        # Blend cloud overlay with change detection
        # Where there are clouds, show gray; where there are changes, show heatmap
        result = colored.copy()
        result[cloud_mask] = cloud_overlay[cloud_mask]
        
        # Add transparency effect to cloud areas (optional)
        alpha = 0.7  # Transparency factor for clouds
        result[cloud_mask] = (alpha * result[cloud_mask] + (1-alpha) * colored[cloud_mask]).astype(np.uint8)
        
        return result
    
    def create_heatmap(self, image1: Image.Image, image2: Image.Image, filename: str, aoi_id: int = None) -> Dict[str, Any]:
        """Create change detection heatmap (unified interface)"""
        return self.create_heatmap_opencv(image1, image2, filename, aoi_id)
    
    def calculate_change_percentage_enhanced(self, image1: Image.Image, image2: Image.Image) -> Dict[str, float]:
        """Calculate enhanced change metrics using OpenCV"""
        try:
            img1_array = np.array(image1)
            img2_array = np.array(image2)
            
            # Handle size mismatch
            if img1_array.shape != img2_array.shape:
                target_height = min(img1_array.shape[0], img2_array.shape[0])
                target_width = min(img1_array.shape[1], img2_array.shape[1])
                img1_array = cv2.resize(img1_array, (target_width, target_height), interpolation=cv2.INTER_LANCZOS4)
                img2_array = cv2.resize(img2_array, (target_width, target_height), interpolation=cv2.INTER_LANCZOS4)
            
            # Apply cloud masking to exclude unreliable pixels
            clean_mask, cloud_mask = self._apply_cloud_mask(img1_array, img2_array)
            usable_pixels = np.sum(clean_mask)
            total_pixels = clean_mask.size
            cloud_coverage = (np.sum(cloud_mask) / total_pixels) * 100
            
            # Convert to different color spaces for comprehensive analysis
            if len(img1_array.shape) == 3:
                # RGB difference (masked)
                diff_rgb = np.abs(img1_array.astype(float) - img2_array.astype(float))
                if usable_pixels > 0:
                    masked_diff_rgb = diff_rgb[clean_mask]
                    rgb_change = (np.mean(masked_diff_rgb) / 255.0) * 100
                else:
                    rgb_change = 0
                
                # HSV difference (better for detecting natural changes) (masked)
                hsv1 = cv2.cvtColor(img1_array, cv2.COLOR_RGB2HSV)
                hsv2 = cv2.cvtColor(img2_array, cv2.COLOR_RGB2HSV)
                diff_hsv = np.abs(hsv1.astype(float) - hsv2.astype(float))
                if usable_pixels > 0:
                    masked_diff_hsv = diff_hsv[clean_mask]
                    hsv_change = (np.mean(masked_diff_hsv) / 255.0) * 100
                else:
                    hsv_change = 0
                
                # Structural similarity using template matching approach
                gray1 = cv2.cvtColor(img1_array, cv2.COLOR_RGB2GRAY)
                gray2 = cv2.cvtColor(img2_array, cv2.COLOR_RGB2GRAY)
            else:
                diff_rgb = np.abs(img1_array.astype(float) - img2_array.astype(float))
                rgb_change = (np.mean(diff_rgb) / 255.0) * 100
                hsv_change = rgb_change  # Same as RGB for grayscale
                gray1 = img1_array
                gray2 = img2_array
            
            # Calculate structural changes (masked)
            diff_structural = cv2.absdiff(gray1, gray2)
            if usable_pixels > 0:
                masked_diff_structural = diff_structural[clean_mask]
                structural_change = (np.mean(masked_diff_structural) / 255.0) * 100
                max_intensity = float(np.max(masked_diff_structural) / 255.0 * 100)
            else:
                structural_change = 0
                max_intensity = 0
            
            # Calculate change area percentage (only consider clean pixels)
            threshold = cv2.threshold(diff_structural, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[0]
            _, binary_diff = cv2.threshold(diff_structural, threshold * 0.5, 255, cv2.THRESH_BINARY)
            # Apply clean mask to change detection
            binary_diff_clean = binary_diff & clean_mask.astype(np.uint8) * 255
            changed_pixels = np.sum(binary_diff_clean > 0)
            area_change_percentage = (changed_pixels / usable_pixels) * 100 if usable_pixels > 0 else 0
            
            return {
                'overall_change': float(rgb_change),
                'color_change': float(hsv_change), 
                'structural_change': float(structural_change),
                'area_changed': float(area_change_percentage),
                'change_intensity': float(max_intensity),
                'cloud_coverage': float(cloud_coverage),
                'usable_area_percent': float((usable_pixels / total_pixels) * 100),
                'analysis_quality': 'high' if cloud_coverage < 20 else 'medium' if cloud_coverage < 50 else 'low'
            }
            
        except Exception as e:
            logger.error(f"Error calculating enhanced change percentage: {str(e)}")
            return {
                'overall_change': 0.0,
                'color_change': 0.0,
                'structural_change': 0.0,
                'area_changed': 0.0,
                'change_intensity': 0.0
            }
    
    def calculate_change_percentage(self, image1: Image.Image, image2: Image.Image) -> float:
        """Calculate change percentage (backward compatible)"""
        metrics = self.calculate_change_percentage_enhanced(image1, image2)
        return metrics['overall_change']
    
    def save_image(self, image: Image.Image, filename: str, aoi_id: int = None, quality: int = 95) -> Dict[str, Any]:
        """Save image to S3 and/or local disk"""
        result = {
            'local_path': None,
            's3_key': None,
            'filename': filename
        }
        
        try:
            # Always save locally as backup
            filepath = os.path.join(Config.IMAGES_DIR, filename)
            image.save(filepath, 'JPEG', quality=quality)
            result['local_path'] = filepath
            logger.info(f"Saved image locally: {filepath}")
            
            # Upload to S3 if available and enabled
            if S3_AVAILABLE and s3_service and s3_service.enabled and aoi_id:
                try:
                    # Determine file type based on filename
                    if 'heatmap' in filename.lower():
                        file_type = 'heatmaps'
                    elif 'current' in filename.lower() or 'baseline' in filename.lower():
                        file_type = 'raw'
                    else:
                        file_type = 'normalized'
                    
                    # Upload to S3
                    s3_result = s3_service.upload_image(
                        image=image,
                        file_type=file_type,
                        aoi_id=str(aoi_id),
                        filename=filename,
                        quality=quality
                    )
                    
                    if s3_result:
                        result['s3_key'] = s3_result['s3_key']
                        logger.info(f"✅ Uploaded to S3: {s3_result['s3_key']}")
                    else:
                        logger.warning(f"❌ Failed to upload {filename} to S3")
                        
                except Exception as e:
                    logger.error(f"S3 upload error for {filename}: {str(e)}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error saving image: {str(e)}")
            return result
    
    def load_baseline_image(self, baseline_filename: str) -> Optional[Image.Image]:
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
    
    def detect_changes_advanced(self, image1: Image.Image, image2: Image.Image) -> Dict[str, Any]:
        """Advanced change detection with feature analysis"""
        try:
            # Convert to OpenCV format
            img1_cv = cv2.cvtColor(np.array(image1), cv2.COLOR_RGB2BGR)
            img2_cv = cv2.cvtColor(np.array(image2), cv2.COLOR_RGB2BGR)
            
            # Resize if needed
            if img1_cv.shape != img2_cv.shape:
                h, w = min(img1_cv.shape[0], img2_cv.shape[0]), min(img1_cv.shape[1], img2_cv.shape[1])
                img1_cv = cv2.resize(img1_cv, (w, h))
                img2_cv = cv2.resize(img2_cv, (w, h))
            
            # Detect keypoints using ORB
            orb = cv2.ORB_create(nfeatures=1000)
            kp1, desc1 = orb.detectAndCompute(img1_cv, None)
            kp2, desc2 = orb.detectAndCompute(img2_cv, None)
            
            # Match features
            if desc1 is not None and desc2 is not None:
                bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
                matches = bf.match(desc1, desc2)
                matches = sorted(matches, key=lambda x: x.distance)
                
                # Feature similarity score
                good_matches = [m for m in matches if m.distance < 50]
                feature_similarity = len(good_matches) / max(len(kp1), len(kp2), 1) * 100
            else:
                feature_similarity = 0.0
            
            # Get quality and change metrics
            quality1 = self.assess_image_quality(image1)
            quality2 = self.assess_image_quality(image2)
            change_metrics = self.calculate_change_percentage_enhanced(image1, image2)
            
            return {
                'feature_similarity': feature_similarity,
                'keypoints_image1': len(kp1) if kp1 else 0,
                'keypoints_image2': len(kp2) if kp2 else 0,
                'image1_quality': quality1,
                'image2_quality': quality2,
                'change_metrics': change_metrics,
                'analysis_confidence': min(100, (feature_similarity + quality1['quality_score'] + quality2['quality_score']) / 3)
            }
            
        except Exception as e:
            logger.error(f"Error in advanced change detection: {str(e)}")
            return {
                'feature_similarity': 0.0,
                'keypoints_image1': 0,
                'keypoints_image2': 0,
                'image1_quality': {},
                'image2_quality': {},
                'change_metrics': {},
                'analysis_confidence': 0.0
            }