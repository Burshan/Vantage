import React, { useState, useEffect } from 'react';
import { 
  MapPin, BarChart3, Zap, TrendingUp, Calendar, AlertTriangle, 
  Clock, Activity, Satellite, ChevronRight, Eye, Globe, 
  Shield, CheckCircle, Expand, ArrowUpRight, RefreshCw,
  Users, Timer, Target, Layers
} from 'lucide-react';

const OverviewTab = ({ aois, analysisHistory, userProfile, user, onTabChange, onCreateAOI, onViewAOIDashboard }) => {
  const [animatedValues, setAnimatedValues] = useState({
    activeAOIs: 0,
    analyses: 0,
    credits: 0,
    alerts: 0
  });

  // Helper functions for analysis
  const getChangeLevel = (percentage) => {
    if (!percentage) return 'unknown';
    if (percentage >= 15) return 'high';
    if (percentage >= 5) return 'medium';
    return 'low';
  };

  // Just use all analysis history without filtering
  const filteredAnalyses = analysisHistory;
  
  // Analysis statistics
  const highChangeAnalyses = filteredAnalyses.filter(a => getChangeLevel(a.change_percentage) === 'high');
  const recentAnalyses = filteredAnalyses.slice(0, 5);
  const activeAOIs = aois.filter(aoi => aoi.is_active);
  const scheduledAOIs = aois.filter(aoi => aoi.next_run_at);

  // Calculate trends
  const averageChange = filteredAnalyses.length > 0 
    ? filteredAnalyses.reduce((sum, a) => sum + (a.change_percentage || 0), 0) / filteredAnalyses.length
    : 0;

  // Professional helper functions
  const getCurrentTime = () => {
    return new Date().toLocaleString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    });
  };

  const getNextScheduledTime = () => {
    if (scheduledAOIs.length === 0) return 'None scheduled';
    
    // Find the earliest next_run_at time
    const nextRun = scheduledAOIs
      .map(aoi => aoi.next_run_at)
      .filter(time => time)
      .sort()
      [0];
    
    if (!nextRun) return 'None scheduled';
    
    return new Date(nextRun).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    });
  };

  const handleViewAnalysis = (analysis) => {
    const aoi = aois.find(a => a.id === analysis.aoi_id);
    if (aoi && onViewAOIDashboard) {
      onViewAOIDashboard(aoi.id);
    }
  };

  // Animation effect for counting up numbers
  useEffect(() => {
    const targetValues = {
      activeAOIs: activeAOIs.length,
      analyses: filteredAnalyses.length,
      credits: userProfile?.tokens_remaining || 0,
      alerts: highChangeAnalyses.length
    };

    const animateValue = (key, target) => {
      const start = 0;
      const duration = 400; // 400ms duration - much snappier
      const startTime = Date.now();

      const animate = () => {
        const elapsed = Date.now() - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        // Easing function for smooth animation
        const easeOut = 1 - Math.pow(1 - progress, 3);
        const current = Math.floor(start + (target - start) * easeOut);
        
        setAnimatedValues(prev => ({ ...prev, [key]: current }));
        
        if (progress < 1) {
          requestAnimationFrame(animate);
        }
      };
      
      requestAnimationFrame(animate);
    };

    // Animate each value
    Object.entries(targetValues).forEach(([key, value]) => {
      animateValue(key, value);
    });
  }, [activeAOIs.length, filteredAnalyses.length, userProfile?.tokens_remaining, highChangeAnalyses.length]);

  return (
    <>
      <div className="space-y-6">
      {/* Simple Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-light text-white tracking-tight">
            Good {new Date().getHours() < 12 ? 'morning' : new Date().getHours() < 17 ? 'afternoon' : 'evening'}, {user?.firstName || userProfile?.first_name || 'User'}
          </h1>
          <p className="text-slate-400 text-sm mt-2 font-medium">Here's what's happening with your satellite monitoring</p>
        </div>
      </div>

      {/* Professional Stats Cards */}
      <div className="grid grid-cols-4 gap-6">
        {/* Active AOIs - Blue theme */}
        <div className="group relative bg-gradient-to-br from-blue-900/30 via-slate-800/80 to-slate-900/90 backdrop-blur-xl border border-blue-500/20 rounded-2xl p-6 text-center hover:border-blue-400/40 transition-all duration-150 shadow-2xl hover:shadow-blue-500/10">
          <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-transparent rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-150"></div>
          <div className="relative z-10">
            <Target className="w-6 h-6 text-blue-400 mx-auto mb-3 group-hover:scale-110 transition-transform duration-150" />
            <div className="text-3xl font-light text-blue-300 mb-2">{animatedValues.activeAOIs}</div>
            <div className="text-sm text-blue-400/80 font-medium tracking-wide uppercase">Active AOIs</div>
          </div>
        </div>
        
        {/* Analyses - Emerald theme */}
        <div className="group relative bg-gradient-to-br from-emerald-900/30 via-slate-800/80 to-slate-900/90 backdrop-blur-xl border border-emerald-500/20 rounded-2xl p-6 text-center hover:border-emerald-400/40 transition-all duration-150 shadow-2xl hover:shadow-emerald-500/10">
          <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/5 to-transparent rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-150"></div>
          <div className="relative z-10">
            <BarChart3 className="w-6 h-6 text-emerald-400 mx-auto mb-3 group-hover:scale-110 transition-transform duration-150" />
            <div className="text-3xl font-light text-emerald-300 mb-2">{animatedValues.analyses}</div>
            <div className="text-sm text-emerald-400/80 font-medium tracking-wide uppercase">Analyses</div>
          </div>
        </div>
        
        {/* Credits - Purple theme */}
        <div className="group relative bg-gradient-to-br from-purple-900/30 via-slate-800/80 to-slate-900/90 backdrop-blur-xl border border-purple-500/20 rounded-2xl p-6 text-center hover:border-purple-400/40 transition-all duration-150 shadow-2xl hover:shadow-purple-500/10">
          <div className="absolute inset-0 bg-gradient-to-br from-purple-500/5 to-transparent rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-150"></div>
          <div className="relative z-10">
            <Zap className="w-6 h-6 text-purple-400 mx-auto mb-3 group-hover:scale-110 transition-transform duration-150" />
            <div className="flex items-center justify-center mb-2">
              <div className="text-3xl font-light text-purple-300">{animatedValues.credits}</div>
              <div className="w-2 h-2 bg-purple-400 rounded-full ml-2 animate-pulse shadow-lg shadow-purple-400/50"></div>
            </div>
            <div className="text-sm text-purple-400/80 font-medium tracking-wide uppercase">Credits</div>
          </div>
        </div>
        
        {/* High Changes - Orange theme */}
        <div className="group relative bg-gradient-to-br from-orange-900/30 via-slate-800/80 to-slate-900/90 backdrop-blur-xl border border-orange-500/20 rounded-2xl p-6 text-center hover:border-orange-400/40 transition-all duration-150 shadow-2xl hover:shadow-orange-500/10">
          <div className="absolute inset-0 bg-gradient-to-br from-orange-500/5 to-transparent rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-150"></div>
          <div className="relative z-10">
            <AlertTriangle className="w-6 h-6 text-orange-400 mx-auto mb-3 group-hover:scale-110 transition-transform duration-150" />
            <div className="text-3xl font-light text-orange-300 mb-2">
              {animatedValues.alerts}
            </div>
            <div className="text-sm text-orange-400/80 font-medium tracking-wide uppercase">
              High Changes
            </div>
          </div>
        </div>
      </div>

      {/* Main Content - Two Column */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Activity */}
        <div className="group bg-gradient-to-br from-slate-800/50 via-slate-800/70 to-slate-900/80 backdrop-blur-xl border border-slate-600/30 rounded-2xl shadow-2xl hover:border-slate-500/50 transition-all duration-150 hover:shadow-slate-900/50">
          <div className="p-6 border-b border-slate-700/50">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-medium text-white tracking-tight">Recent Activity</h3>
              <button 
                onClick={() => onTabChange('results')}
                className="text-blue-400 hover:text-blue-300 text-sm font-medium transition-colors duration-100 hover:scale-105"
              >
                View all
              </button>
            </div>
          </div>
          
          <div className="p-6">
            {recentAnalyses.slice(0, 3).length > 0 ? (
              <div className="space-y-4">
                {recentAnalyses.slice(0, 3).map((analysis, index) => {
                  const changeLevel = getChangeLevel(analysis.change_percentage);
                  const aoi = aois.find(a => a.id === analysis.aoi_id);
                  
                  return (
                    <div 
                      key={analysis.id} 
                      onClick={() => handleViewAnalysis(analysis)}
                      className="flex items-center justify-between p-4 bg-slate-700/30 backdrop-blur border border-slate-600/30 rounded-xl hover:bg-slate-700/50 hover:border-slate-600/50 cursor-pointer transition-all duration-150 hover:shadow-lg"
                    >
                      <div className="flex items-center space-x-4">
                        <div className={`w-3 h-3 rounded-full shadow-lg ${
                          changeLevel === 'high' ? 'bg-red-400 shadow-red-400/50' : 
                          changeLevel === 'medium' ? 'bg-amber-400 shadow-amber-400/50' : 
                          'bg-emerald-400 shadow-emerald-400/50'
                        }`}></div>
                        <div>
                          <div className="text-sm font-medium text-white">{aoi?.name || 'Unknown AOI'}</div>
                          <div className="text-xs text-slate-400 mt-0.5">
                            {new Date(analysis.analysis_timestamp).toLocaleDateString()}
                          </div>
                        </div>
                      </div>
                      <div className="text-sm font-medium text-slate-300">
                        {analysis.change_percentage?.toFixed(1)}%
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="text-center py-8 text-slate-400 text-sm">
                No recent activity
              </div>
            )}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="group bg-gradient-to-br from-slate-800/50 via-slate-800/70 to-slate-900/80 backdrop-blur-xl border border-slate-600/30 rounded-2xl shadow-2xl hover:border-slate-500/50 transition-all duration-150 hover:shadow-slate-900/50">
          <div className="px-6 py-5 border-b border-slate-700/50">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-gradient-to-r from-emerald-500/20 to-blue-500/20 rounded-lg">
                  <Zap className="w-4 h-4 text-emerald-400" />
                </div>
                <h3 className="text-lg font-semibold text-white tracking-tight">Quick Actions</h3>
              </div>
              <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse shadow-emerald-400/50 shadow-lg"></div>
            </div>
          </div>
          
          <div className="p-6">
            <div className="space-y-4">
              {/* Primary Action - Create AOI */}
              <button 
                onClick={() => {
                  if (!userProfile || userProfile.tokens_remaining <= 0) {
                    return;
                  }
                  onTabChange('aois');
                  setTimeout(() => onCreateAOI && onCreateAOI(), 100);
                }}
                disabled={!userProfile || userProfile.tokens_remaining <= 0}
                title={!userProfile || userProfile.tokens_remaining <= 0 ? "Need 1 token to create AOI" : "Create new Area of Interest"}
                className="relative w-full bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 disabled:from-gray-600 disabled:to-gray-700 text-white py-4 px-6 rounded-xl text-sm font-semibold transition-all duration-150 flex items-center justify-center space-x-3 shadow-lg shadow-blue-500/30 hover:shadow-xl hover:shadow-blue-500/40 hover:scale-[1.02] disabled:hover:scale-100 disabled:cursor-not-allowed overflow-hidden group"
              >
                <div className="absolute inset-0 bg-gradient-to-r from-white/10 via-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-150"></div>
                <MapPin className="w-5 h-5 flex-shrink-0 relative z-10" />
                <span className="font-semibold relative z-10">
                  {(!userProfile || userProfile.tokens_remaining <= 0) ? 'No Tokens Available' : 'Create New AOI'}
                </span>
              </button>
              
              {/* Secondary Actions Grid */}
              <div className="grid grid-cols-2 gap-3">
                <button 
                  onClick={() => onTabChange('aois')}
                  className="btn-action relative bg-gradient-to-br from-slate-700/70 to-slate-800/80 hover:from-slate-600/80 hover:to-slate-700/90 border border-slate-600/40 hover:border-slate-500/60 text-white py-4 px-4 rounded-xl text-sm font-medium transition-all duration-150 flex flex-col items-center justify-center space-y-2 backdrop-blur hover:scale-[1.02] hover:shadow-lg overflow-hidden group"
                >
                  <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-150"></div>
                  <div className="relative z-10 flex items-center justify-center">
                    <div className="icon-container p-2 bg-gradient-to-br from-slate-600/60 to-slate-700/80 rounded-lg transition-all duration-100">
                      <RefreshCw className="RefreshCw w-5 h-5 text-slate-300 transition-all duration-150" />
                    </div>
                    {activeAOIs.length > 0 && (
                      <div className="absolute -top-1 -right-1 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-full w-5 h-5 text-xs font-bold flex items-center justify-center shadow-lg">
                        {activeAOIs.length}
                      </div>
                    )}
                  </div>
                  <span className="text-xs font-medium text-center relative z-10">Manage AOIs</span>
                </button>
                
                <button 
                  onClick={() => onTabChange('results')}
                  className="btn-action relative bg-gradient-to-br from-slate-700/70 to-slate-800/80 hover:from-slate-600/80 hover:to-slate-700/90 border border-slate-600/40 hover:border-slate-500/60 text-white py-4 px-4 rounded-xl text-sm font-medium transition-all duration-150 flex flex-col items-center justify-center space-y-2 backdrop-blur hover:scale-[1.02] hover:shadow-lg overflow-hidden group"
                >
                  <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-150"></div>
                  <div className="icon-container p-2 bg-gradient-to-br from-slate-600/60 to-slate-700/80 rounded-lg transition-all duration-100 relative z-10">
                    <BarChart3 className="BarChart3 w-5 h-5 text-slate-300 transition-all duration-150" />
                  </div>
                  <span className="text-xs font-medium text-center relative z-10">View Results</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Alert Banner */}
      {highChangeAnalyses.length > 0 && (
        <div className="group bg-gradient-to-r from-orange-900/30 via-red-900/20 to-pink-900/30 backdrop-blur-xl border border-orange-500/30 hover:border-orange-400/50 rounded-2xl p-6 shadow-2xl hover:shadow-orange-500/20 transition-all duration-150">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="p-2 bg-amber-500/20 rounded-xl">
                <AlertTriangle className="w-6 h-6 text-amber-400" />
              </div>
              <div>
                <div className="text-base font-medium text-white mb-1">
                  {highChangeAnalyses.length} high change alert{highChangeAnalyses.length !== 1 ? 's' : ''}
                </div>
                <div className="text-sm text-amber-300/80">
                  Significant changes detected requiring attention
                </div>
              </div>
            </div>
            <button 
              onClick={() => onTabChange('results')}
              className="bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white px-6 py-2.5 rounded-xl text-sm font-medium transition-all duration-150 shadow-lg shadow-amber-500/25 hover:shadow-xl hover:shadow-amber-500/30 hover:scale-105"
            >
              Review
            </button>
          </div>
        </div>
      )}
      </div>
    </>
  );
};

export default OverviewTab;