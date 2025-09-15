import React, { useState } from 'react';
import { TrendingUp, CheckCircle, Calendar, Satellite, BarChart3, Expand, MapPin, Clock, AlertTriangle, Filter } from 'lucide-react';
import ImageGallery from '../common/ImageGallery';

const AnalysisResultsTab = ({ analysisResults, analysisHistory, aois, onViewAOIs }) => {
  const [galleryOpen, setGalleryOpen] = useState(false);
  const [galleryInitialIndex, setGalleryInitialIndex] = useState(0);
  const [galleryImages, setGalleryImages] = useState([]);
  const [filterLevel, setFilterLevel] = useState('all'); // 'all', 'high', 'medium', 'low'

  // Helper function to get change level
  const getChangeLevel = (percentage) => {
    if (!percentage) return 'unknown';
    if (percentage >= 15) return 'high';
    if (percentage >= 5) return 'medium';
    return 'low';
  };

  const getChangeLevelColor = (level) => {
    switch (level) {
      case 'high': return 'text-red-400 bg-red-900/20 border-red-800';
      case 'medium': return 'text-yellow-400 bg-yellow-900/20 border-yellow-800';
      case 'low': return 'text-green-400 bg-green-900/20 border-green-800';
      default: return 'text-gray-400 bg-gray-900/20 border-gray-800';
    }
  };

  // Get recent analyses (last 20)
  const recentAnalyses = analysisHistory ? analysisHistory.slice(0, 20) : [];

  // Filter analyses by change level
  const filteredAnalyses = recentAnalyses.filter(analysis => {
    if (filterLevel === 'all') return true;
    return getChangeLevel(analysis.change_percentage) === filterLevel;
  });

  // Group analyses by AOI
  const analysisGroups = {};
  filteredAnalyses.forEach(analysis => {
    if (!analysis.aoi_id) return;
    if (!analysisGroups[analysis.aoi_id]) {
      analysisGroups[analysis.aoi_id] = [];
    }
    analysisGroups[analysis.aoi_id].push(analysis);
  });

  // Prepare gallery images from specific analysis
  const openGallery = (analysis) => {
    const images = [];
    
    // Add baseline image (first in display order)
    if (analysis.images?.baseline_url) {
      images.push({
        url: `${analysis.images.baseline_url}`,
        title: 'Baseline Image',
        description: 'Historical baseline image for comparison',
        metadata: {
          Type: 'Baseline',
          Date: new Date(analysis.analysis_timestamp).toLocaleDateString(),
          AOI: aois?.find(aoi => aoi.id === analysis.aoi_id)?.name || 'Unknown AOI'
        }
      });
    }
    
    // Add current image (second in display order)
    if (analysis.images?.current_url) {
      images.push({
        url: `${analysis.images.current_url}`,
        title: 'Current Satellite Image',
        description: 'Latest satellite imagery for comparison',
        metadata: {
          Type: 'Current Image',
          Date: new Date(analysis.analysis_timestamp).toLocaleDateString(),
          AOI: aois?.find(aoi => aoi.id === analysis.aoi_id)?.name || 'Unknown AOI'
        }
      });
    }
    
    // Add heatmap (third in display order)
    if (analysis.images?.heatmap_url) {
      images.push({
        url: `${analysis.images.heatmap_url}`,
        title: 'Change Detection Heatmap',
        description: `Analysis from ${new Date(analysis.analysis_timestamp).toLocaleDateString()}`,
        metadata: {
          Type: 'Change Detection',
          'Change %': analysis.change_percentage ? `${analysis.change_percentage.toFixed(2)}%` : 'N/A',
          Date: new Date(analysis.analysis_timestamp).toLocaleDateString(),
          AOI: aois?.find(aoi => aoi.id === analysis.aoi_id)?.name || 'Unknown AOI'
        }
      });
    }
    
    setGalleryImages(images);
    setGalleryInitialIndex(0);
    setGalleryOpen(true);
  };

  if (!recentAnalyses || recentAnalyses.length === 0) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-3xl font-light text-white tracking-tight">Analysis Results</h2>
            <p className="text-slate-400 text-sm mt-2 font-medium">Review your satellite analysis outcomes</p>
          </div>
        </div>
        <div className="bg-gradient-to-br from-slate-800/60 to-slate-900/60 backdrop-blur border border-slate-700/40 rounded-2xl p-12 text-center shadow-2xl">
          <div className="p-4 bg-slate-700/30 rounded-2xl inline-block mb-6">
            <TrendingUp className="w-16 h-16 text-slate-400" />
          </div>
          <h3 className="text-white text-xl font-medium mb-3 tracking-tight">No Analysis Results</h3>
          <p className="text-slate-400 mb-8 max-w-md mx-auto leading-relaxed">Run an analysis on an AOI to view results here</p>
          <button
            onClick={onViewAOIs}
            className="bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white px-8 py-3 rounded-xl font-medium transition-all duration-300 shadow-lg shadow-blue-500/25 hover:shadow-xl hover:shadow-blue-500/30 hover:scale-[1.02]"
          >
            View AOIs
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Premium Header with Filters */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-light text-white tracking-tight">Analysis Results</h2>
          <p className="text-slate-400 text-sm mt-2 font-medium">Review your satellite analysis outcomes</p>
        </div>
        <div className="flex items-center space-x-4">
          <span className="text-sm text-slate-400 font-medium">Filter by change level:</span>
          <div className="flex items-center bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-xl p-1">
            {[
              { key: 'all', label: 'All', count: recentAnalyses.length },
              { key: 'high', label: 'High', count: recentAnalyses.filter(a => getChangeLevel(a.change_percentage) === 'high').length },
              { key: 'medium', label: 'Medium', count: recentAnalyses.filter(a => getChangeLevel(a.change_percentage) === 'medium').length },
              { key: 'low', label: 'Low', count: recentAnalyses.filter(a => getChangeLevel(a.change_percentage) === 'low').length }
            ].map(filter => (
              <button
                key={filter.key}
                onClick={() => setFilterLevel(filter.key)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200 ${
                  filterLevel === filter.key 
                    ? 'bg-blue-500/90 text-white shadow-lg shadow-blue-500/25' 
                    : 'text-slate-300 hover:text-white hover:bg-slate-700/50'
                }`}
              >
                {filter.label} ({filter.count})
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Premium Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-gradient-to-br from-slate-800/80 to-slate-900/80 backdrop-blur border border-slate-700/50 rounded-2xl p-6 hover:border-slate-600/50 transition-all duration-300 shadow-xl">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-400 text-sm font-medium tracking-wide">Total Analyses</p>
              <p className="text-3xl font-light text-white mt-2">{recentAnalyses.length}</p>
            </div>
            <div className="p-3 bg-blue-500/20 rounded-2xl">
              <BarChart3 className="w-8 h-8 text-blue-400" />
            </div>
          </div>
        </div>
        
        <div className="bg-gradient-to-br from-slate-800/80 to-slate-900/80 backdrop-blur border border-slate-700/50 rounded-2xl p-6 hover:border-slate-600/50 transition-all duration-300 shadow-xl">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-400 text-sm font-medium tracking-wide">High Changes</p>
              <p className="text-3xl font-light text-red-400 mt-2">
                {recentAnalyses.filter(a => getChangeLevel(a.change_percentage) === 'high').length}
              </p>
            </div>
            <div className="p-3 bg-red-500/20 rounded-2xl">
              <AlertTriangle className="w-8 h-8 text-red-400" />
            </div>
          </div>
        </div>
        
        <div className="bg-gradient-to-br from-slate-800/80 to-slate-900/80 backdrop-blur border border-slate-700/50 rounded-2xl p-6 hover:border-slate-600/50 transition-all duration-300 shadow-xl">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-400 text-sm font-medium tracking-wide">Active AOIs</p>
              <p className="text-3xl font-light text-white mt-2">{Object.keys(analysisGroups).length}</p>
            </div>
            <div className="p-3 bg-emerald-500/20 rounded-2xl">
              <MapPin className="w-8 h-8 text-emerald-400" />
            </div>
          </div>
        </div>
        
        <div className="bg-gradient-to-br from-slate-800/80 to-slate-900/80 backdrop-blur border border-slate-700/50 rounded-2xl p-6 hover:border-slate-600/50 transition-all duration-300 shadow-xl">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-400 text-sm font-medium tracking-wide">Latest Analysis</p>
              <p className="text-sm font-medium text-white mt-2">
                {recentAnalyses.length > 0 ? new Date(recentAnalyses[0].analysis_timestamp).toLocaleDateString() : 'N/A'}
              </p>
            </div>
            <div className="p-3 bg-purple-500/20 rounded-2xl">
              <Clock className="w-8 h-8 text-purple-400" />
            </div>
          </div>
        </div>
      </div>

      {/* Analysis Results by AOI */}
      {Object.keys(analysisGroups).length > 0 ? (
        <div className="space-y-6">
          {Object.entries(analysisGroups).map(([aoiId, analyses]) => {
            const aoi = aois?.find(a => a.id === parseInt(aoiId));
            const latestAnalysis = analyses[0];
            const changeLevel = getChangeLevel(latestAnalysis.change_percentage);
            
            return (
              <div key={aoiId} className="bg-gradient-to-br from-slate-800/60 to-slate-900/60 backdrop-blur border border-slate-700/40 rounded-2xl shadow-2xl">
                <div className="p-6 border-b border-slate-700/50">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <div className="p-2 bg-blue-500/20 rounded-xl">
                        <MapPin className="w-5 h-5 text-blue-400" />
                      </div>
                      <div>
                        <h3 className="text-lg font-medium text-white tracking-tight">{aoi?.name || `AOI ${aoiId}`}</h3>
                        <p className="text-sm text-slate-400 mt-0.5">{aoi?.location_name}</p>
                      </div>
                      <div className={`px-4 py-2 rounded-full text-xs font-medium backdrop-blur border ${
                        changeLevel === 'high' ? 'bg-red-500/20 text-red-300 border-red-500/30' : 
                        changeLevel === 'medium' ? 'bg-amber-500/20 text-amber-300 border-amber-500/30' : 
                        'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
                      }`}>
                        Latest: {changeLevel} change
                      </div>
                    </div>
                    <div className="text-right text-sm text-slate-400 font-medium">
                      {analyses.length} analyses
                    </div>
                  </div>
                </div>
                
                <div className="p-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                    {analyses.slice(0, 6).map((analysis, index) => {
                      const level = getChangeLevel(analysis.change_percentage);
                      return (
                        <div key={analysis.id} className={`bg-slate-700/20 backdrop-blur rounded-lg p-4 transition-all duration-300 hover:bg-slate-700/40 border-l-2 ${
                          level === 'high' ? 'border-l-red-400' : 
                          level === 'medium' ? 'border-l-amber-400' : 
                          'border-l-emerald-400'
                        }`}>
                          <div className="flex items-center justify-between mb-3">
                            <div className="text-sm text-white font-medium">
                              {new Date(analysis.analysis_timestamp).toLocaleDateString()}
                            </div>
                            <div className={`text-xs font-semibold px-2 py-1 rounded ${
                              level === 'high' ? 'text-red-300' : 
                              level === 'medium' ? 'text-amber-300' : 
                              'text-emerald-300'
                            }`}>
                              {analysis.change_percentage ? `${analysis.change_percentage.toFixed(1)}%` : 'N/A'}
                            </div>
                          </div>
                          
                          {analysis.images?.heatmap_url && (
                            <button
                              onClick={() => openGallery(analysis)}
                              className="w-full bg-slate-600/40 hover:bg-slate-500/60 text-white text-xs py-2 px-3 rounded-md transition-all duration-300 flex items-center justify-center space-x-2 mb-3"
                            >
                              <Expand className="w-3 h-3" />
                              <span>View Images</span>
                            </button>
                          )}
                          
                          <div className="text-xs text-slate-400">
                            {new Date(analysis.analysis_timestamp).toLocaleTimeString()}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                  
                  {analyses.length > 6 && (
                    <div className="mt-6 text-center">
                      <button className="text-blue-400 hover:text-blue-300 text-sm font-medium transition-colors duration-200 hover:scale-105">
                        View {analyses.length - 6} more analyses
                      </button>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="bg-gradient-to-br from-slate-800/60 to-slate-900/60 backdrop-blur border border-slate-700/40 rounded-2xl p-12 text-center shadow-2xl">
          <div className="p-4 bg-slate-700/30 rounded-2xl inline-block mb-6">
            <Filter className="w-12 h-12 text-slate-400" />
          </div>
          <p className="text-slate-300 text-lg font-medium mb-2">No analyses found for the selected filter</p>
          <p className="text-slate-400 text-sm">Try selecting "All" to see all available analyses</p>
        </div>
      )}

      {/* Image Gallery */}
      <ImageGallery
        images={galleryImages}
        isOpen={galleryOpen}
        onClose={() => setGalleryOpen(false)}
        initialIndex={galleryInitialIndex}
      />
    </div>
  );
};

export default AnalysisResultsTab;