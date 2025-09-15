import React, { useState, useEffect } from 'react';
import { useUser, UserButton } from '@clerk/clerk-react';
import { Bell } from 'lucide-react';

// Layout Components
import Navigation from './components/layout/Navigation';

// Dashboard Components
import OverviewTab from './components/dashboard/OverviewTab';
import AnalysisResultsTab from './components/dashboard/AnalysisResultsTab';
import HistoryTab from './components/dashboard/HistoryTab';
import TokenManagementTab from './components/dashboard/TokenManagementTab';
import SettingsTab from './components/dashboard/SettingsTab';
import AdminPanel from './components/admin/AdminPanel';

// AOI Components
import AOIsTab from './components/aoi/AOIsTab';
import CreateAOIWithMap from './components/aoi/CreateAOIWithMap';
import AOIDashboardView from './components/aoi/AOIDashboardView';

// Common Components
import LoadingSpinner from './components/common/LoadingSpinner';
import ProcessingOverlay from './components/common/ProcessingOverlay';
import ToastContainer from './components/common/ToastContainer';

// Hooks
import useVantageAPI from './hooks/useVantageAPI';
import useToast from './hooks/useToast';
import useOptimizedAOI from './hooks/useOptimizedAOI';

const VantageDashboard = () => {
  const { user } = useUser();
  const { apiCall } = useVantageAPI();
  const toast = useToast();

  // State management
  const [userProfile, setUserProfile] = useState(null);
  const [analysisHistory, setAnalysisHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [showCreateAOI, setShowCreateAOI] = useState(false);
  const [analysisResults, setAnalysisResults] = useState(null);
  
  // AOI Dashboard view state
  const [aoiDashboard, setAoiDashboard] = useState(null);
  const [showAOIDashboard, setShowAOIDashboard] = useState(false);

  // Use optimized AOI hook
  const { 
    aois, 
    isProcessing, 
    createAOI: createAOIOptimized, 
    deleteAOI: deleteAOIOptimized, 
    runAnalysis: runAnalysisOptimized,
    scheduleMonitoring: scheduleMonitoringOptimized,
    loadAOIs 
  } = useOptimizedAOI([], toast);

  useEffect(() => {
    initializeDashboard();
    
    // Check if we should restore AOI dashboard from URL
    const urlParams = new URLSearchParams(window.location.search);
    const aoiId = urlParams.get('aoi');
    if (aoiId) {
      // Delay loading AOI dashboard until after initial data is loaded
      setTimeout(() => {
        loadAOIDashboard(parseInt(aoiId));
      }, 1000);
    }
  }, []);

  const initializeDashboard = async () => {
    setIsLoading(true);
    try {
      await Promise.all([
        loadUserProfile(),
        loadAOIs(),
        loadAnalysisHistory()
      ]);
    } catch (error) {
      console.error('Error initializing dashboard:', error);
      toast.showError('Failed to initialize dashboard');
    } finally {
      setIsLoading(false);
    }
  };

  const loadUserProfile = async () => {
    try {
      const response = await apiCall('/api/user/profile');
      console.log('🔍 loadUserProfile response:', response);
      // Handle both old and new response formats
      const userData = response.data?.user || response.user || response;
      console.log('🔍 extracted userData:', userData);
      setUserProfile(userData);
    } catch (error) {
      console.error('Error loading profile:', error);
      toast.showError('Failed to load user profile');
    }
  };

  const loadAnalysisHistory = async () => {
    try {
      const response = await apiCall('/api/user/history?limit=20');
      console.log('🔍 loadAnalysisHistory response:', response);
      // Handle both old and new response formats
      const historyData = response.data?.history || response.history || response;
      console.log('🔍 extracted historyData:', historyData);
      setAnalysisHistory(historyData || []);
    } catch (error) {
      console.error('Error loading history:', error);
      setAnalysisHistory([]);
      toast.showError('Failed to load analysis history');
    }
  };

  const loadAOIDashboard = async (aoiId) => {
    setIsLoading(true);
    try {
      const response = await apiCall(`/api/aoi/${aoiId}/dashboard`);
      console.log('🔍 loadAOIDashboard response:', response);
      // Handle both old and new response formats
      const dashboardData = response.data?.dashboard || response.dashboard || response;
      console.log('🔍 extracted dashboardData:', dashboardData);
      setAoiDashboard(dashboardData);
      setShowAOIDashboard(true);
      
      // Update URL to maintain state on refresh
      const url = new URL(window.location);
      url.searchParams.set('aoi', aoiId);
      window.history.replaceState({}, '', url);
    } catch (error) {
      console.error('Error loading AOI dashboard:', error);
      toast.showError('Failed to load AOI dashboard: ' + error.message);
    } finally {
      setIsLoading(false);
    }
  };

  const [isAnalyzing, setIsAnalyzing] = useState(false);
  
  const runManualAnalysis = async (aoiId, analysisType = 'baseline_comparison') => {
    setIsAnalyzing(true);
    try {
      const data = await runAnalysisOptimized(aoiId, analysisType);
      setAnalysisResults(data);
      
      // Reload data to get updated tokens and history
      await Promise.all([
        loadUserProfile(),
        loadAnalysisHistory(),
        loadAOIDashboard(aoiId)
      ]);
      
      toast.showInfo('Check the Analysis Results tab to view your results');
    } catch (error) {
      // Error handling is done in the runAnalysisOptimized function
      // Just reload user profile in case tokens were consumed
      try {
        await Promise.all([
          loadUserProfile(),
          loadAnalysisHistory()
        ]);
      } catch (reloadError) {
        console.error('Failed to reload data after analysis error:', reloadError);
      }
    } finally {
      setIsAnalyzing(false);
    }
  };

  const scheduleMonitoring = async (aoiId, frequency) => {
    try {
      await scheduleMonitoringOptimized(aoiId, frequency);
      await loadAOIDashboard(aoiId);
    } catch (error) {
      // Error already handled in scheduleMonitoringOptimized
    }
  };

  const createAOI = async (formData) => {
    try {
      // Map new format to old format expected by useOptimizedAOI
      const mappedData = {
        name: formData.name,
        description: formData.description,
        location: formData.location_name,
        classification: formData.classification,
        priority: formData.priority,
        color: '#3B82F6', // Default color since new form doesn't have this field
        coords: formData.bbox_coordinates
      };
      
      await createAOIOptimized(mappedData);
      setShowCreateAOI(false);
      // Only reload user profile for token count - AOIs already updated optimistically
      await loadUserProfile();
    } catch (error) {
      // Error already handled in useOptimizedAOI hook
    }
  };

  const deleteAOI = async (aoiId) => {
    if (!confirm('Are you sure you want to delete this AOI? This action cannot be undone.')) return;
    
    try {
      await deleteAOIOptimized(aoiId);
      // AOI already removed optimistically
    } catch (error) {
      // Error already handled in useOptimizedAOI hook
    }
  };


  // Event handlers
  const handleTabChange = (tabId) => {
    setActiveTab(tabId);
    
    // If we're in AOI dashboard, exit it when navigating to a different tab
    if (showAOIDashboard) {
      setShowAOIDashboard(false);
      setAoiDashboard(null);
      
      // Clear AOI parameter from URL
      const url = new URL(window.location);
      url.searchParams.delete('aoi');
      window.history.replaceState({}, '', url);
    }
  };

  const handleCreateAOI = () => {
    if (!userProfile || userProfile.tokens_remaining <= 0) {
      toast.showWarning('Insufficient tokens to create AOI. You need 1 token to create an AOI.');
      return;
    }
    setShowCreateAOI(true);
  };

  const handleCloseCreateAOI = () => {
    setShowCreateAOI(false);
  };

  const handleBackFromDashboard = () => {
    setShowAOIDashboard(false);
    setAoiDashboard(null);
    
    // Clear AOI parameter from URL
    const url = new URL(window.location);
    url.searchParams.delete('aoi');
    window.history.replaceState({}, '', url);
  };

  const handleViewAOIs = () => {
    setActiveTab('aois');
  };

  if (isLoading) {
    return <LoadingSpinner />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <Navigation 
        activeTab={activeTab} 
        onTabChange={handleTabChange} 
        isInAOIDashboard={showAOIDashboard}
        userProfile={userProfile}
      />

      {/* Professional Header Bar */}
      <div className="lg:pl-64 fixed top-0 left-0 right-0 z-30 bg-gradient-to-r from-slate-900/98 via-slate-800/98 to-slate-900/98 backdrop-blur-xl border-b border-slate-700/30 shadow-2xl">
        {/* Top accent line */}
        <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-blue-500/50 via-emerald-500/50 to-purple-500/50"></div>
        
        <div className="flex items-center justify-between h-16 px-6">
          <div className="flex items-center space-x-6">
            {showAOIDashboard && aoiDashboard?.aoi ? (
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse"></div>
                  <div className="text-xs text-slate-400 font-medium uppercase tracking-wider">Active AOI</div>
                </div>
                <div className="h-6 w-px bg-slate-600/50"></div>
                <div className="flex items-center space-x-2">
                  <div className="text-sm font-semibold text-white">{aoiDashboard.aoi.name}</div>
                  <div className="px-2 py-0.5 bg-blue-500/20 border border-blue-500/30 rounded-full">
                    <span className="text-xs font-medium text-blue-400">LIVE</span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex items-center space-x-3">
                <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse"></div>
                <div className="text-sm font-medium text-slate-300">Dashboard Overview</div>
              </div>
            )}
          </div>
          
          <div className="flex items-center space-x-4">
            {/* System Status Indicator */}
            <div className="hidden lg:flex items-center space-x-3">
              <div className="flex items-center space-x-2 text-xs">
                <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse"></div>
                <span className="text-emerald-400 font-medium">All Systems</span>
              </div>
              <div className="text-xs text-slate-500">|</div>
              <div className="text-xs text-slate-400">
                {new Date().toLocaleString('en-US', { 
                  hour: '2-digit', 
                  minute: '2-digit',
                  hour12: false 
                })} UTC
              </div>
            </div>
            
            {/* Credits Display */}
            {userProfile && (
              <div className="hidden sm:flex items-center space-x-3">
                <div className="flex items-center space-x-3 bg-gradient-to-r from-slate-800/60 to-slate-700/60 backdrop-blur border border-slate-600/30 rounded-xl px-4 py-2 shadow-lg">
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse shadow-emerald-400/50 shadow-lg"></div>
                    <span className="text-emerald-300 font-bold text-sm">{userProfile.tokens_remaining || 0}</span>
                  </div>
                  <div className="text-xs text-slate-400 uppercase tracking-wide font-medium">Credits</div>
                </div>
              </div>
            )}
            
            {/* Action Buttons */}
            <div className="flex items-center space-x-2">
              <button className="relative p-2.5 text-slate-400 hover:text-white hover:bg-slate-700/50 rounded-xl transition-all duration-200 group">
                <Bell className="w-5 h-5" />
                <div className="absolute top-2 right-2 w-2 h-2 bg-blue-400 rounded-full opacity-0 group-hover:opacity-100 animate-ping"></div>
              </button>
              
              <div className="w-px h-6 bg-gradient-to-b from-transparent via-slate-600 to-transparent"></div>
              
              <UserButton 
                appearance={{
                  elements: {
                    avatarBox: "w-10 h-10 rounded-xl shadow-lg hover:shadow-xl transition-shadow duration-150",
                    userButtonPopoverCard: "bg-slate-800/95 backdrop-blur-xl border border-slate-700/50 shadow-2xl rounded-xl",
                    userButtonPopoverActionButton: "text-slate-300 hover:text-white hover:bg-slate-700/60 rounded-lg transition-all duration-200",
                    userButtonPopoverActionButtonText: "text-slate-300 font-medium",
                    userButtonPopoverFooter: "bg-slate-900/80 border-t border-slate-700/50 backdrop-blur"
                  }
                }}
                showName={false}
              />
            </div>
          </div>
        </div>
        
        {/* Bottom accent line */}
        <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-slate-600/50 to-transparent"></div>
      </div>

      {/* Main Content Area - Adjusted for sidebar and top bar */}
      <main className="lg:pl-64 pt-16 min-h-screen">
        <div className="py-6 px-4 sm:px-6 lg:px-8">
        {showAOIDashboard ? (
          <AOIDashboardView
            aoiDashboard={aoiDashboard}
            onBack={handleBackFromDashboard}
            onRunAnalysis={runManualAnalysis}
            onScheduleMonitoring={scheduleMonitoring}
            isProcessing={isAnalyzing}
            userProfile={userProfile}
          />
        ) : (
          <>
            {activeTab === 'overview' && (
              <OverviewTab
                aois={aois}
                analysisHistory={analysisHistory}
                userProfile={userProfile}
                user={user}
                onTabChange={handleTabChange}
                onCreateAOI={handleCreateAOI}
                onViewAOIDashboard={loadAOIDashboard}
              />
            )}

            {activeTab === 'aois' && (
              <AOIsTab
                aois={aois}
                analysisHistory={analysisHistory}
                userProfile={userProfile}
                onCreateAOI={handleCreateAOI}
                onViewDashboard={loadAOIDashboard}
                onDeleteAOI={deleteAOI}
                isProcessing={isProcessing}
              />
            )}

            {activeTab === 'results' && (
              <AnalysisResultsTab
                analysisResults={analysisResults}
                analysisHistory={analysisHistory}
                aois={aois}
                onViewAOIs={handleViewAOIs}
              />
            )}

            {activeTab === 'history' && (
              <HistoryTab analysisHistory={analysisHistory} />
            )}

            {activeTab === 'tokens' && (
              <TokenManagementTab
                userProfile={userProfile}
                aoisCount={aois.length}
              />
            )}

            {activeTab === 'settings' && (
              <SettingsTab
                userProfile={userProfile}
              />
            )}

            {activeTab === 'admin' && (
              <AdminPanel userProfile={userProfile} />
            )}
          </>
        )}
        </div>
      </main>

      <CreateAOIWithMap
        isOpen={showCreateAOI}
        onClose={handleCloseCreateAOI}
        onSubmit={createAOI}
        isProcessing={isProcessing}
      />

      <ProcessingOverlay isVisible={isProcessing} />
      
      <ToastContainer toasts={toast.toasts} onHideToast={toast.hideToast} />
    </div>
  );
};

export default VantageDashboard;