"""
Date Strategy Utilities
Centralized logic for satellite image date selection
"""
from datetime import datetime, timedelta
from typing import Tuple, Dict, Any
import logging

logger = logging.getLogger(__name__)


class SatelliteDateStrategy:
    """
    Manages date selection strategy for satellite image analysis
    """
    
    @staticmethod
    def get_analysis_dates(analysis_date: datetime = None, 
                          baseline_offset_days: int = 365,
                          baseline_window_days: int = 7,
                          current_window_days: int = 3) -> Dict[str, str]:
        """
        Get optimized date ranges for satellite analysis using rolling window approach
        
        Args:
            analysis_date: Date of analysis (defaults to now)
            baseline_offset_days: Days back for baseline (default: 365 = 1 year)
            baseline_window_days: Window around baseline date for cloud coverage (±days)
            current_window_days: Window around current date for cloud coverage (±days)
            
        Returns:
            Dict with date strings for satellite API calls
        """
        if analysis_date is None:
            analysis_date = datetime.now()
        
        # Calculate baseline date (rolling with analysis date)
        baseline_date = analysis_date - timedelta(days=baseline_offset_days)
        
        # Create windows for better cloud coverage
        baseline_from = baseline_date - timedelta(days=baseline_window_days)
        baseline_to = baseline_date + timedelta(days=baseline_window_days)
        
        current_from = analysis_date - timedelta(days=current_window_days)
        current_to = analysis_date + timedelta(days=current_window_days)
        
        result = {
            'baseline_from': baseline_from.strftime("%Y-%m-%d"),
            'baseline_to': baseline_to.strftime("%Y-%m-%d"),
            'current_from': current_from.strftime("%Y-%m-%d"),
            'current_to': current_to.strftime("%Y-%m-%d"),
            'analysis_date': analysis_date.strftime("%Y-%m-%d"),
            'baseline_center': baseline_date.strftime("%Y-%m-%d")
        }
        
        logger.info(f"📅 Analysis dates calculated: baseline={result['baseline_center']} (±{baseline_window_days}d), current={result['analysis_date']} (±{current_window_days}d)")
        
        return result
    
    @staticmethod
    def get_aoi_creation_dates(creation_date: datetime = None,
                              baseline_window_days: int = 14) -> Dict[str, str]:
        """
        Get date range for AOI baseline image creation
        Uses a wider window for initial baseline to ensure good image quality
        
        Args:
            creation_date: AOI creation date (defaults to now)
            baseline_window_days: Window for finding clear baseline image
            
        Returns:
            Dict with date strings for baseline image creation
        """
        if creation_date is None:
            creation_date = datetime.now()
        
        # For AOI creation, use 1 year ago as baseline reference point
        baseline_date = creation_date - timedelta(days=365)
        
        # Wider window for initial baseline creation (better chance of clear image)
        baseline_from = baseline_date - timedelta(days=baseline_window_days)
        baseline_to = baseline_date + timedelta(days=baseline_window_days)
        
        result = {
            'baseline_from': baseline_from.strftime("%Y-%m-%d"),
            'baseline_to': baseline_to.strftime("%Y-%m-%d"),
            'baseline_center': baseline_date.strftime("%Y-%m-%d"),
            'creation_date': creation_date.strftime("%Y-%m-%d")
        }
        
        logger.info(f"📅 AOI baseline dates: {result['baseline_center']} (±{baseline_window_days}d)")
        
        return result
    
    @staticmethod
    def get_manual_comparison_dates(analysis_date: datetime = None) -> Dict[str, str]:
        """
        Get sensible default dates for manual comparison analysis
        
        Args:
            analysis_date: Date of analysis (defaults to now)
            
        Returns:
            Dict with date strings for manual comparison
        """
        if analysis_date is None:
            analysis_date = datetime.now()
        
        # Period 1: 1 year ago (1 month window)
        period1_center = analysis_date - timedelta(days=365)
        period1_from = period1_center - timedelta(days=15)
        period1_to = period1_center + timedelta(days=15)
        
        # Period 2: Recent (2 weeks window)
        period2_center = analysis_date
        period2_from = period2_center - timedelta(days=7)
        period2_to = period2_center + timedelta(days=7)
        
        result = {
            'date1_from': period1_from.strftime("%Y-%m-%d"),
            'date1_to': period1_to.strftime("%Y-%m-%d"),
            'date2_from': period2_from.strftime("%Y-%m-%d"),
            'date2_to': period2_to.strftime("%Y-%m-%d"),
            'period1_center': period1_center.strftime("%Y-%m-%d"),
            'period2_center': period2_center.strftime("%Y-%m-%d")
        }
        
        logger.info(f"📅 Manual comparison: {result['period1_center']} vs {result['period2_center']}")
        
        return result
    
    @staticmethod
    def get_monitoring_dates(last_analysis_date: datetime,
                           current_date: datetime = None) -> Dict[str, str]:
        """
        Get dates for scheduled monitoring analysis
        Compares last analysis to current state
        
        Args:
            last_analysis_date: Date of previous analysis
            current_date: Current date (defaults to now)
            
        Returns:
            Dict with date strings for monitoring comparison
        """
        if current_date is None:
            current_date = datetime.now()
        
        # Small windows for monitoring (we want recent changes)
        baseline_from = last_analysis_date - timedelta(days=3)
        baseline_to = last_analysis_date + timedelta(days=3)
        
        current_from = current_date - timedelta(days=3)
        current_to = current_date + timedelta(days=3)
        
        result = {
            'baseline_from': baseline_from.strftime("%Y-%m-%d"),
            'baseline_to': baseline_to.strftime("%Y-%m-%d"),
            'current_from': current_from.strftime("%Y-%m-%d"),
            'current_to': current_to.strftime("%Y-%m-%d"),
            'last_analysis': last_analysis_date.strftime("%Y-%m-%d"),
            'current_analysis': current_date.strftime("%Y-%m-%d")
        }
        
        logger.info(f"📅 Monitoring comparison: {result['last_analysis']} vs {result['current_analysis']}")
        
        return result


# Convenience function for backward compatibility
def get_satellite_dates(analysis_date: datetime = None) -> Tuple[str, str, str, str]:
    """
    Backward compatible function returning baseline and current date ranges
    
    Returns:
        Tuple of (baseline_from, baseline_to, current_from, current_to)
    """
    dates = SatelliteDateStrategy.get_analysis_dates(analysis_date)
    return (
        dates['baseline_from'],
        dates['baseline_to'], 
        dates['current_from'],
        dates['current_to']
    )