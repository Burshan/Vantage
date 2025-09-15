import React, { useState, useEffect } from 'react';
import { 
  ArrowLeft, Play, Monitor, BarChart3, Zap, CheckCircle, 
  Activity, Satellite, TrendingUp, Expand, Calendar, Clock 
} from 'lucide-react';
import { useAuth } from '@clerk/clerk-react';
import ImageGallery from '../common/ImageGallery';
import TrendGallery from '../common/TrendGallery';
import SchedulePopup from '../common/SchedulePopup';
import useVantageAPI from '../../hooks/useVantageAPI';
import { API_BASE_URL, buildFullURL } from '../../config/api';

const AOIDashboardView = ({ 
  aoiDashboard, 
  onBack, 
  onRunAnalysis, 
  onScheduleMonitoring, 
  isProcessing,
  userProfile
}) => {
  const { getToken, userId, isSignedIn } = useAuth();
  const { apiCall } = useVantageAPI();
  const [galleryOpen, setGalleryOpen] = useState(false);
  const [galleryImages, setGalleryImages] = useState([]);
  const [galleryInitialIndex, setGalleryInitialIndex] = useState(0);
  const [trendGalleryOpen, setTrendGalleryOpen] = useState(false);
  const [showSchedulePopup, setShowSchedulePopup] = useState(false);
  const [currentSchedule, setCurrentSchedule] = useState(null);
  const [isLoadingSchedule, setIsLoadingSchedule] = useState(false);
  const [authDebug, setAuthDebug] = useState('');

  if (!aoiDashboard) return null;

  const aoi = aoiDashboard.aoi;
  const stats = aoiDashboard.statistics;
  const baseline = aoiDashboard.baseline;
  const recentAnalyses = aoiDashboard.recent_analyses || [];

  // Helper function to construct proper image URLs
  const getImageURL = (imageUrl) => {
    if (!imageUrl) return null;
    // If already a full URL, return as-is (don't double-process)
    if (imageUrl.startsWith('http')) return imageUrl;
    if (imageUrl.startsWith('/')) return `${API_BASE_URL}${imageUrl}`;
    return `${API_BASE_URL}/${imageUrl}`;
  };

  // Load current schedule on component mount
  useEffect(() => {
    if (aoi?.id) {
      checkAuthAndLoadSchedule();
    }
  }, [aoi?.id]);

  const checkAuthAndLoadSchedule = async () => {
    try {
      const token = await getToken({ skipCache: true });
      const debugInfo = `Auth Status: ${isSignedIn ? '✅' : '❌'} | User: ${userId || 'None'} | Token: ${token ? 'Present' : 'Missing'}`;
      setAuthDebug(debugInfo);
      console.log('🔐', debugInfo);
      
      if (!token) {
        console.error('❌ No authentication token available');
        return;
      }
      
      loadCurrentSchedule();
    } catch (error) {
      console.error('❌ Auth check failed:', error);
      setAuthDebug(`Auth Error: ${error.message}`);
    }
  };

  const loadCurrentSchedule = async () => {
    setIsLoadingSchedule(true);
    try {
      const data = await apiCall(`/api/aoi/${aoi.id}/schedule-monitoring`);
      console.log('🔍 Schedule API Response:', data);
      console.log('🔍 Conditions: success =', data.success, 'has_schedule =', data.has_schedule);
      
      if (data.success && data.has_schedule) {
        console.log('✅ Setting currentSchedule to:', data);
        setCurrentSchedule(data);
      } else {
        console.log('❌ Setting currentSchedule to null because:', 
          !data.success ? 'success is false' : 'has_schedule is false');
        setCurrentSchedule(null);
      }
    } catch (error) {
      console.error('Failed to load schedule:', error);
      setCurrentSchedule(null);
    } finally {
      setIsLoadingSchedule(false);
    }
  };

  const handleScheduleSave = async (aoiId, scheduleData) => {
    try {
      console.log('📡 AOIDashboardView.handleScheduleSave called with:', { aoiId, scheduleData });
      
      // Check auth first
      const token = await getToken({ skipCache: true });
      if (!token) {
        throw new Error('Authentication required. Please refresh the page and try again.');
      }
      
      const result = await apiCall(`/api/aoi/${aoiId}/schedule-monitoring`, {
        method: 'POST',
        body: JSON.stringify(scheduleData)
      });

      console.log('📥 Backend response:', result);

      // Reload the current schedule to get fresh data
      console.log('🔄 Reloading schedule...');
      await loadCurrentSchedule();
      
      // Note: We don't call the parent's onScheduleMonitoring because:
      // 1. We already handle the scheduling in this component
      // 2. The parent function might use different logic that conflicts with our popup
      // 3. We already reload the current schedule to update the UI
      
      console.log('✅ handleScheduleSave completed');
    } catch (error) {
      console.error('❌ handleScheduleSave error:', error);
      
      // If it's an auth error, refresh token and retry once
      if (error.message.includes('NO_AUTH_HEADER') || error.message.includes('authorization')) {
        try {
          console.log('🔄 Auth error detected, refreshing token and retrying...');
          const freshToken = await getToken({ skipCache: true });
          if (freshToken) {
            // Retry the call
            const result = await apiCall(`/api/aoi/${aoiId}/schedule-monitoring`, {
              method: 'POST',
              body: JSON.stringify(scheduleData)
            });
            await loadCurrentSchedule();
            return;
          }
        } catch (retryError) {
          console.error('❌ Retry also failed:', retryError);
        }
      }
      
      throw error; // Let the popup handle the error display
    }
  };

  // Process baseline image URL once to avoid double-processing
  const baselineImageUrl = baseline.image_url ? getImageURL(baseline.image_url) : null;

  const openAnalysisGallery = (analysis) => {
    const images = [];
    
    // Add baseline image (first in display order)
    if (baselineImageUrl) {
      images.push({
        url: baselineImageUrl,
        title: 'Baseline Image',
        description: `Original baseline image for ${aoi.name}`,
        metadata: {
          Type: 'Baseline',
          Date: baseline.date ? new Date(baseline.date).toLocaleDateString() : 'Unknown',
          Location: aoi.location_name
        }
      });
    }

    // Add current analysis image (second in display order) - using current_url
    if (analysis.images?.current_url) {
      images.push({
        url: getImageURL(analysis.images.current_url),
        title: `${analysis.operation_name} - Current Image`,
        description: `Current satellite image captured for analysis`,
        metadata: {
          Type: 'Current Image',
          Date: new Date(analysis.analysis_timestamp).toLocaleDateString(),
          Time: new Date(analysis.analysis_timestamp).toLocaleTimeString()
        }
      });
    }

    // Add analysis heatmap (third in display order)
    if (analysis.images?.heatmap_url) {
      images.push({
        url: getImageURL(analysis.images.heatmap_url),
        title: `${analysis.operation_name} - Change Detection`,
        description: `Change detection analysis performed on ${new Date(analysis.analysis_timestamp).toLocaleDateString()}`,
        metadata: {
          Type: 'Change Detection',
          'Change %': analysis.change_percentage ? `${analysis.change_percentage.toFixed(2)}%` : 'N/A',
          Date: new Date(analysis.analysis_timestamp).toLocaleDateString(),
          Time: new Date(analysis.analysis_timestamp).toLocaleTimeString()
        }
      });
    }

    setGalleryImages(images);
    setGalleryInitialIndex(0);
    setGalleryOpen(true);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <button
            onClick={onBack}
            className="mr-4 p-2 text-gray-400 hover:text-white transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h2 className="text-2xl font-bold text-white">{aoi.name}</h2>
            <p className="text-gray-400">{aoi.location_name}</p>
          </div>
        </div>
        
        <div className="flex space-x-3">
          <button
            onClick={() => onRunAnalysis(aoi.id)}
            disabled={!userProfile?.tokens_remaining || isProcessing}
            className="bg-green-600 hover:bg-green-700 disabled:bg-gray-600 text-white px-4 py-2 rounded flex items-center"
            title={!userProfile?.tokens_remaining ? "Insufficient tokens" : "Run satellite analysis (1 token) - Note: Server has known session issues"}
          >
            <Play className="w-4 h-4 mr-2" />
            {isProcessing ? 'Analyzing...' : 'Run Analysis'}
          </button>

          <button
            onClick={() => setTrendGalleryOpen(true)}
            disabled={recentAnalyses.length < 2}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white px-4 py-2 rounded flex items-center"
            title={recentAnalyses.length < 2 ? "Need at least 2 analyses to show trends" : "View trend analysis of changes over time"}
          >
            <TrendingUp className="w-4 h-4 mr-2" />
            View Trend ({recentAnalyses.length})
          </button>
          
          <button
            onClick={() => setShowSchedulePopup(true)}
            disabled={isProcessing}
            className="bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 text-white px-4 py-2 rounded flex items-center"
            title={currentSchedule ? "Update scheduled analysis" : "Schedule analysis"}
          >
            {currentSchedule ? (
              <>
                <Calendar className="w-4 h-4 mr-2" />
                Update Schedule
              </>
            ) : (
              <>
                <Monitor className="w-4 h-4 mr-2" />
                Schedule Analysis
              </>
            )}
          </button>
        </div>
      </div>

      {/* AOI Info Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Total Analyses</p>
              <p className="text-2xl font-bold text-white">{stats.total_analyses}</p>
            </div>
            <BarChart3 className="w-8 h-8 text-blue-400" />
          </div>
        </div>
        
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Tokens Used</p>
              <p className="text-2xl font-bold text-white">{stats.total_tokens_used}</p>
            </div>
            <Zap className="w-8 h-8 text-yellow-400" />
          </div>
        </div>
        
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Baseline Status</p>
              <p className="text-sm font-bold text-white">{baseline.status}</p>
            </div>
            <CheckCircle className={`w-8 h-8 ${baseline.status === 'completed' ? 'text-green-400' : 'text-gray-400'}`} />
          </div>
        </div>
        
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Monitor Status</p>
              <p className="text-sm font-bold text-white">{stats.monitoring_status}</p>
            </div>
            <Activity className={`w-8 h-8 ${stats.monitoring_status === 'active' ? 'text-green-400' : 'text-gray-400'}`} />
          </div>
        </div>
      </div>

      {/* Current Schedule Info */}
      {currentSchedule && currentSchedule.next_run_at && (
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
            <Clock className="w-5 h-5 mr-2 text-purple-400" />
            Scheduled Analysis
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <p className="text-gray-400 text-sm">Next Run</p>
              <p className="text-white font-medium">
                {new Date(currentSchedule.next_run_at).toLocaleString('en-US', {
                  timeZone: 'UTC',
                  year: 'numeric',
                  month: 'short', 
                  day: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit'
                })} UTC
              </p>
            </div>
            <div>
              <p className="text-gray-400 text-sm">Frequency</p>
              <p className="text-white font-medium capitalize">
                {currentSchedule.monitoring_frequency || 'Once'}
              </p>
            </div>
            <div>
              <p className="text-gray-400 text-sm">Status</p>
              <p className={`font-medium ${currentSchedule.is_active ? 'text-green-400' : 'text-red-400'}`}>
                {currentSchedule.is_active ? 'Active' : 'Disabled'}
              </p>
            </div>
          </div>
          <div className="mt-4 flex gap-2">
            <button
              onClick={() => setShowSchedulePopup(true)}
              className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm"
            >
              Modify
            </button>
            <button
              onClick={async () => {
                if (window.confirm('Remove scheduled analysis?')) {
                  try {
                    await handleScheduleSave(aoi.id, { 
                      enabled: false,
                      frequency: 'none'
                    });
                    // handleScheduleSave already calls loadCurrentSchedule()
                  } catch (error) {
                    console.error('Failed to remove schedule:', error);
                  }
                }
              }}
              className="bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded text-sm"
            >
              Remove
            </button>
          </div>
        </div>
      )}

      {/* Baseline Image */}
      {baseline.image_url && (
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center justify-between">
            <div className="flex items-center">
              <Satellite className="w-5 h-5 mr-2" />
              Baseline Image
            </div>
            <button
              onClick={() => openAnalysisGallery({ images: {} })}
              className="p-1 text-gray-400 hover:text-white transition-colors"
              title="View in gallery"
            >
              <Expand className="w-4 h-4" />
            </button>
          </h3>
          {/* Centered container for the image */}
          <div className="flex justify-center">
            <div className="max-w-md w-full">
              <div 
                className="relative cursor-pointer group"
                onClick={() => openAnalysisGallery({ images: {} })}
              >
                <img 
                  src={baselineImageUrl}
                  alt="Baseline satellite image"
                  className="w-full rounded border border-slate-600 transition-transform group-hover:scale-105 shadow-lg"
                  onError={(e) => {
                    console.error('Failed to load baseline image:', baseline.image_url);
                    e.target.style.display = 'none';
                  }}
                  onLoad={() => console.log('✅ Baseline image loaded successfully')}
                />
                <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-30 rounded transition-all flex items-center justify-center">
                  <Expand className="w-8 h-8 text-white opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>
              </div>
              <p className="text-gray-400 text-sm mt-2 text-center">
                Created: {baseline.date ? new Date(baseline.date).toLocaleDateString() : 'Unknown'}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Recent Analyses */}
      <div className="bg-slate-800 border border-slate-700 rounded-lg">
        <div className="p-6 border-b border-slate-700">
          <h3 className="text-lg font-semibold text-white flex items-center">
            <TrendingUp className="w-5 h-5 mr-2" />
            Recent Analyses
          </h3>
        </div>
        
        {recentAnalyses.length > 0 ? (
          <div className="divide-y divide-slate-700">
            {recentAnalyses.map(analysis => (
              <div key={analysis.id} className="p-4 hover:bg-slate-700/50 transition-colors">
                <div className="flex justify-between items-start">
                  <div>
                    <div className="text-white font-medium">{analysis.operation_name}</div>
                    <div className="text-gray-400 text-sm">
                      {new Date(analysis.analysis_timestamp).toLocaleString()}
                    </div>
                    {analysis.change_percentage && (
                      <div className="text-blue-400 text-sm">
                        Change: {analysis.change_percentage.toFixed(2)}%
                      </div>
                    )}
                    <div className="text-gray-500 text-xs">
                      {[
                        baseline.image_url && 'Baseline',
                        analysis.images?.current_url && 'Current',
                        analysis.images?.heatmap_url && 'Heatmap'
                      ].filter(Boolean).join(' • ')} available
                    </div>
                  </div>
                  
                  <div className="flex space-x-2">
                    {analysis.images.current_url && (
                      <div 
                        className="relative cursor-pointer group"
                        onClick={() => openAnalysisGallery(analysis)}
                        title="Current image - Click to view in gallery"
                      >
                        <img 
                          src={getImageURL(analysis.images.current_url)}
                          alt="Current satellite image"
                          className="w-16 h-16 rounded border border-slate-600 object-cover transition-transform group-hover:scale-110"
                          onError={(e) => {
                            console.error('Failed to load current image:', analysis.images.current_url);
                            e.target.style.opacity = '0.3';
                          }}
                        />
                        <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-50 rounded transition-all flex items-center justify-center">
                          <Expand className="w-4 h-4 text-white opacity-0 group-hover:opacity-100 transition-opacity" />
                        </div>
                      </div>
                    )}
                    {analysis.images.heatmap_url && (
                      <div 
                        className="relative cursor-pointer group"
                        onClick={() => openAnalysisGallery(analysis)}
                        title="Change heatmap - Click to view in gallery"
                      >
                        <img 
                          src={getImageURL(analysis.images.heatmap_url)}
                          alt="Change detection heatmap"
                          className="w-16 h-16 rounded border border-slate-600 object-cover transition-transform group-hover:scale-110"
                          onError={(e) => {
                            console.error('Failed to load heatmap:', analysis.images.heatmap_url);
                            e.target.style.opacity = '0.3';
                          }}
                        />
                        <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-50 rounded transition-all flex items-center justify-center">
                          <Expand className="w-4 h-4 text-white opacity-0 group-hover:opacity-100 transition-opacity" />
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-8 text-center">
            <TrendingUp className="w-12 h-12 text-gray-400 mx-auto mb-3" />
            <p className="text-gray-400">No analyses yet</p>
          </div>
        )}
      </div>

      {/* Image Gallery */}
      <ImageGallery
        images={galleryImages}
        isOpen={galleryOpen}
        onClose={() => setGalleryOpen(false)}
        initialIndex={galleryInitialIndex}
      />

      {/* Trend Gallery */}
      <TrendGallery
        analyses={recentAnalyses}
        isOpen={trendGalleryOpen}
        onClose={() => setTrendGalleryOpen(false)}
        aoi={aoi}
      />

      {/* Schedule Popup */}
      <SchedulePopup
        isOpen={showSchedulePopup}
        onClose={() => setShowSchedulePopup(false)}
        onSave={handleScheduleSave}
        aoiId={aoi?.id}
        currentSchedule={currentSchedule}
      />

      {/* Debug Info */}
      {authDebug && (
        <div className="fixed bottom-4 left-4 bg-slate-800 border border-slate-600 rounded px-3 py-2 text-xs text-gray-300 max-w-md">
          🔐 {authDebug}
        </div>
      )}
    </div>
  );
};

export default AOIDashboardView;