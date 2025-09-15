import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useAuth, useUser, UserButton } from '@clerk/clerk-react';
import { 
  MapPin, Plus, Calendar, TrendingUp, Settings, 
  AlertTriangle, CheckCircle, Eye, Trash2, Edit3,
  Activity, BarChart3, Globe, Satellite, Zap, Play,
  Clock, Monitor, X, ArrowLeft
} from 'lucide-react';
import { API_BASE_URL } from './config/api';
import ApiDebug from './components/debug/ApiDebug';
import useVantageAPI from './hooks/useVantageAPI';

const VantageDashboard = () => {
  const { getToken } = useAuth();
  const { user } = useUser();
  const { apiCall } = useVantageAPI(); // Use centralized API hook
  const [userProfile, setUserProfile] = useState(null);
  const [aois, setAois] = useState([]);
  const [analysisHistory, setAnalysisHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isProcessing, setIsProcessing] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  const [showCreateAOI, setShowCreateAOI] = useState(false);
  const [selectedAOI, setSelectedAOI] = useState(null);
  const [analysisResults, setAnalysisResults] = useState(null);
  
  // NEW: AOI Dashboard view state
  const [aoiDashboard, setAoiDashboard] = useState(null);
  const [showAOIDashboard, setShowAOIDashboard] = useState(false);

  // Use refs to prevent cursor jumping
  const nameRef = useRef('');
  const descriptionRef = useRef('');
  const locationRef = useRef('');
  const classificationRef = useRef('CONFIDENTIAL');
  const priorityRef = useRef('MEDIUM');
  const colorRef = useRef('#3B82F6');
  const coordsRef = useRef([34.876149, 50.964594, 34.911741, 51.025335]);

  const resetForm = () => {
    nameRef.current = '';
    descriptionRef.current = '';
    locationRef.current = '';
    classificationRef.current = 'CONFIDENTIAL';
    priorityRef.current = 'MEDIUM';
    colorRef.current = '#3B82F6';
    coordsRef.current = [34.876149, 50.964594, 34.911741, 51.025335];
  };

  useEffect(() => {
    initializeDashboard();
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
    } finally {
      setIsLoading(false);
    }
  };


  const loadUserProfile = async () => {
    try {
      console.log('🚀 Starting loadUserProfile...');
      console.log('🔍 apiCall function:', typeof apiCall, apiCall);
      const response = await apiCall('/api/user/profile');
      console.log('🔍 Profile API response:', response);
      console.log('🔍 Response type:', typeof response);
      console.log('🔍 Response.data:', response.data);
      console.log('🔍 Response.success:', response.success);
      
      // Handle new MVC response format
      const userData = response.data?.user || response.user || response;
      console.log('👤 Final userData to set:', userData);
      console.log('👤 userData.tokens_remaining:', userData?.tokens_remaining);
      
      setUserProfile(userData);
      console.log('✅ setUserProfile called with:', userData);
      
      // Force a re-render check
      setTimeout(() => {
        console.log('⏰ Checking userProfile after state update...');
        console.log('Current userProfile state should be:', userData);
      }, 100);
      
    } catch (error) {
      console.error('❌ Error loading profile:', error);
    }
  };

  const loadAOIs = async () => {
    try {
      console.log('Loading AOIs...');
      const response = await apiCall('/api/aoi');
      console.log('🔍 AOI API response:', response);
      // Handle new MVC response format
      const aoiData = response.data?.areas_of_interest || response.areas_of_interest || response;
      console.log('🗺️ Setting AOIs:', aoiData);
      setAois(Array.isArray(aoiData) ? aoiData : []);
    } catch (error) {
      console.error('Error loading AOIs:', error);
      setAois([]);
    }
  };

  const loadAnalysisHistory = async () => {
    try {
      const response = await apiCall('/api/user/history?limit=20');
      console.log('🔍 History API response:', response);
      // Handle new MVC response format
      const historyData = response.data?.history || response.history || response;
      console.log('📊 Setting analysis history:', historyData);
      setAnalysisHistory(Array.isArray(historyData) ? historyData : []);
    } catch (error) {
      console.error('Error loading history:', error);
      setAnalysisHistory([]);
    }
  };

  // NEW: Load AOI Dashboard (view only)
  const loadAOIDashboard = async (aoiId) => {
    setIsLoading(true);
    try {
      const data = await apiCall(`/api/aoi/${aoiId}/dashboard`);
      setAoiDashboard(data.dashboard);
      setSelectedAOI(aoiId);
      setShowAOIDashboard(true);
    } catch (error) {
      console.error('Error loading AOI dashboard:', error);
      alert('Failed to load AOI dashboard: ' + error.message);
    } finally {
      setIsLoading(false);
    }
  };

  // NEW: Run Manual Analysis (separate from view)
  const runManualAnalysis = async (aoiId, analysisType = 'baseline_comparison') => {
    if (!userProfile || userProfile.tokens_remaining <= 0) {
      alert('Insufficient tokens for analysis');
      return;
    }

    setIsProcessing(true);
    try {
      const data = await apiCall(`/api/aoi/${aoiId}/run-analysis`, {
        method: 'POST',
        body: JSON.stringify({ analysis_type: analysisType })
      });

      setAnalysisResults(data);
      
      // Reload data
      await Promise.all([
        loadUserProfile(),
        loadAnalysisHistory(),
        loadAOIDashboard(aoiId) // Refresh dashboard
      ]);
      
      alert('Analysis completed successfully!');
    } catch (error) {
      alert('Analysis failed: ' + error.message);
    } finally {
      setIsProcessing(false);
    }
  };

  // NEW: Schedule Monitoring
  const scheduleMonitoring = async (aoiId, frequency) => {
    setIsProcessing(true);
    try {
      await apiCall(`/api/aoi/${aoiId}/schedule-monitoring`, {
        method: 'POST',
        body: JSON.stringify({ frequency, enabled: true })
      });
      
      // Reload dashboard
      await loadAOIDashboard(aoiId);
      alert(`Monitoring scheduled for ${frequency} frequency`);
    } catch (error) {
      alert('Failed to schedule monitoring: ' + error.message);
    } finally {
      setIsProcessing(false);
    }
  };

  const createAOI = async () => {
    if (!nameRef.current.trim()) {
      alert('Please enter an AOI name');
      return;
    }

    if (!coordsRef.current || coordsRef.current.length !== 4) {
      alert('Please enter valid bounding box coordinates');
      return;
    }

    setIsProcessing(true);
    try {
      const aoiData = {
        name: nameRef.current,
        description: descriptionRef.current,
        location_name: locationRef.current,
        bbox_coordinates: coordsRef.current,
        classification: classificationRef.current,
        priority: priorityRef.current,
        color_code: colorRef.current,
        monitoring_frequency: 'WEEKLY'
      };

      await apiCall('/api/aoi', {
        method: 'POST',
        body: JSON.stringify(aoiData)
      });
      
      setShowCreateAOI(false);
      resetForm();
      
      await Promise.all([
        loadAOIs(),
        loadUserProfile()
      ]);
      
      alert('AOI created successfully!');
    } catch (error) {
      alert('Failed to create AOI: ' + error.message);
    } finally {
      setIsProcessing(false);
    }
  };

  const deleteAOI = async (aoiId) => {
    if (!confirm('Are you sure you want to delete this AOI? This action cannot be undone.')) return;
    
    setIsProcessing(true);
    try {
      await apiCall(`/api/aoi/${aoiId}`, { method: 'DELETE' });
      await loadAOIs();
      alert('AOI deleted successfully');
    } catch (error) {
      alert('Failed to delete AOI: ' + error.message);
    } finally {
      setIsProcessing(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-white text-lg">Loading VANTAGE System...</p>
          <p className="text-gray-400 text-sm">Initializing satellite intelligence platform</p>
        </div>
      </div>
    );
  }

  // NEW: AOI Dashboard Component
  const AOIDashboardView = () => {
    if (!aoiDashboard) return null;

    const aoi = aoiDashboard.aoi;
    const stats = aoiDashboard.statistics;
    const baseline = aoiDashboard.baseline;
    const recentAnalyses = aoiDashboard.recent_analyses || [];

    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <button
              onClick={() => {
                setShowAOIDashboard(false);
                setAoiDashboard(null);
              }}
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
              onClick={() => runManualAnalysis(aoi.id)}
              disabled={!aoiDashboard.actions_available?.can_run_analysis || isProcessing}
              className="bg-green-600 hover:bg-green-700 disabled:bg-gray-600 text-white px-4 py-2 rounded flex items-center"
            >
              <Play className="w-4 h-4 mr-2" />
              Run Analysis
            </button>
            
            <button
              onClick={() => scheduleMonitoring(aoi.id, 'weekly')}
              disabled={isProcessing}
              className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white px-4 py-2 rounded flex items-center"
            >
              <Monitor className="w-4 h-4 mr-2" />
              Schedule
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

        {/* Baseline Image */}
        {baseline.image_url && (
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
              <Satellite className="w-5 h-5 mr-2" />
              Baseline Image
            </h3>
            <div className="max-w-md">
              <img 
                src={`http://localhost:5000${baseline.image_url}`}
                alt="Baseline"
                className="w-full rounded border border-slate-600"
              />
              <p className="text-gray-400 text-sm mt-2">
                Created: {baseline.date ? new Date(baseline.date).toLocaleDateString() : 'Unknown'}
              </p>
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
                    </div>
                    
                    <div className="flex space-x-2">
                      {analysis.images.heatmap_url && (
                        <img 
                          src={`http://localhost:5000${analysis.images.heatmap_url}`}
                          alt="Analysis result"
                          className="w-16 h-16 rounded border border-slate-600 object-cover"
                        />
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
      </div>
    );
  };

  const AOICard = ({ aoi }) => {
    const lastAnalysis = analysisHistory.find(h => h.aoi?.name === aoi.name);
    
    return (
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 hover:border-slate-600 transition-colors">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center">
            <div 
              className="w-4 h-4 rounded-full mr-3 border-2 border-white/20"
              style={{ backgroundColor: aoi.color_code }}
            />
            <div>
              <h3 className="text-white font-semibold text-lg">{aoi.name}</h3>
              <p className="text-gray-400 text-sm">{aoi.location_name}</p>
            </div>
          </div>
          
          <div className="flex space-x-2">
            {/* CHANGED: View button now loads dashboard instead of running analysis */}
            <button
              onClick={() => loadAOIDashboard(aoi.id)}
              disabled={isProcessing}
              className="p-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded transition-colors"
              title="View AOI Dashboard"
            >
              <Eye className="w-4 h-4" />
            </button>
            <button
              onClick={() => deleteAOI(aoi.id)}
              disabled={isProcessing}
              className="p-2 bg-red-600 hover:bg-red-700 disabled:bg-gray-600 text-white rounded transition-colors"
              title="Delete AOI"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        </div>
        
        <p className="text-gray-300 text-sm mb-4 line-clamp-2">{aoi.description}</p>
        
        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-gray-400 text-sm">Classification:</span>
            <span className={`px-2 py-1 text-xs rounded ${
              aoi.classification === 'TOP_SECRET' ? 'bg-red-900 text-red-300' :
              aoi.classification === 'SECRET' ? 'bg-orange-900 text-orange-300' :
              aoi.classification === 'CONFIDENTIAL' ? 'bg-yellow-900 text-yellow-300' :
              'bg-green-900 text-green-300'
            }`}>
              {aoi.classification}
            </span>
          </div>
          
          <div className="flex justify-between items-center">
            <span className="text-gray-400 text-sm">Priority:</span>
            <span className={`px-2 py-1 text-xs rounded ${
              aoi.priority === 'CRITICAL' ? 'bg-red-900 text-red-300' :
              aoi.priority === 'HIGH' ? 'bg-orange-900 text-orange-300' :
              aoi.priority === 'MEDIUM' ? 'bg-yellow-900 text-yellow-300' :
              'bg-green-900 text-green-300'
            }`}>
              {aoi.priority}
            </span>
          </div>
          
          <div className="border-t border-slate-700 pt-3">
            <div className="flex justify-between items-center text-sm">
              <span className="text-gray-400">Last Analysis:</span>
              <span className="text-white">
                {lastAnalysis ? new Date(lastAnalysis.analysis_timestamp).toLocaleDateString() : 'Never'}
              </span>
            </div>
            <div className="flex justify-between items-center text-sm mt-2">
              <span className="text-gray-400">Baseline Status:</span>
              <span className={`text-sm ${aoi.baseline_status === 'completed' ? 'text-green-400' : 'text-yellow-400'}`}>
                {aoi.baseline_status || 'pending'}
              </span>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const CreateAOIModal = () => {
    const [localName, setLocalName] = useState(nameRef.current);
    const [localDescription, setLocalDescription] = useState(descriptionRef.current);
    const [localLocation, setLocalLocation] = useState(locationRef.current);
    const [localClassification, setLocalClassification] = useState(classificationRef.current);
    const [localPriority, setLocalPriority] = useState(priorityRef.current);
    const [localColor, setLocalColor] = useState(colorRef.current);
    const [localCoords, setLocalCoords] = useState([...coordsRef.current]);

    const handleSubmit = () => {
      nameRef.current = localName;
      descriptionRef.current = localDescription;
      locationRef.current = localLocation;
      classificationRef.current = localClassification;
      priorityRef.current = localPriority;
      colorRef.current = localColor;
      coordsRef.current = [...localCoords];
      
      createAOI();
    };

    const handleClose = () => {
      setShowCreateAOI(false);
      resetForm();
    };

    const handleCoordinateChange = (index, value) => {
      const newCoords = [...localCoords];
      newCoords[index] = parseFloat(value) || 0;
      setLocalCoords(newCoords);
    };

    return (
      <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
        <div className="bg-slate-800 border border-slate-700 rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
          <div className="p-6 border-b border-slate-700">
            <h2 className="text-xl font-bold text-white">Create New Area of Interest</h2>
            <p className="text-gray-400 text-sm mt-1">Define a geographic area for automated satellite monitoring</p>
          </div>
          
          <div className="p-6 space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">AOI Name *</label>
                <input
                  type="text"
                  value={localName}
                  onChange={(e) => setLocalName(e.target.value)}
                  className="w-full p-3 bg-slate-700 border border-slate-600 rounded text-white placeholder-gray-400"
                  placeholder="e.g., Tehran Industrial Complex"
                  disabled={isProcessing}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Location Name</label>
                <input
                  type="text"
                  value={localLocation}
                  onChange={(e) => setLocalLocation(e.target.value)}
                  className="w-full p-3 bg-slate-700 border border-slate-600 rounded text-white placeholder-gray-400"
                  placeholder="Geographic identifier"
                  disabled={isProcessing}
                />
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Description</label>
              <textarea
                value={localDescription}
                onChange={(e) => setLocalDescription(e.target.value)}
                className="w-full p-3 bg-slate-700 border border-slate-600 rounded text-white placeholder-gray-400 h-24"
                placeholder="Describe the strategic importance and monitoring objectives..."
                disabled={isProcessing}
              />
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Classification</label>
                <select
                  value={localClassification}
                  onChange={(e) => setLocalClassification(e.target.value)}
                  className="w-full p-3 bg-slate-700 border border-slate-600 rounded text-white"
                  disabled={isProcessing}
                >
                  <option value="UNCLASSIFIED">Unclassified</option>
                  <option value="CONFIDENTIAL">Confidential</option>
                  <option value="SECRET">Secret</option>
                  <option value="TOP_SECRET">Top Secret</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Priority</label>
                <select
                  value={localPriority}
                  onChange={(e) => setLocalPriority(e.target.value)}
                  className="w-full p-3 bg-slate-700 border border-slate-600 rounded text-white"
                  disabled={isProcessing}
                >
                  <option value="LOW">Low</option>
                  <option value="MEDIUM">Medium</option>
                  <option value="HIGH">High</option>
                  <option value="CRITICAL">Critical</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Color Code</label>
                <input
                  type="color"
                  value={localColor}
                  onChange={(e) => setLocalColor(e.target.value)}
                  className="w-full h-12 bg-slate-700 border border-slate-600 rounded cursor-pointer"
                  disabled={isProcessing}
                />
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Bounding Box Coordinates</label>
              <p className="text-xs text-gray-400 mb-3">Enter coordinates in decimal degrees: [lat_min, lon_min, lat_max, lon_max]</p>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {['Lat Min', 'Lon Min', 'Lat Max', 'Lon Max'].map((label, index) => (
                  <div key={index}>
                    <label className="block text-xs text-gray-400 mb-1">{label}</label>
                    <input
                      type="number"
                      step="0.000001"
                      value={localCoords[index]}
                      onChange={(e) => handleCoordinateChange(index, e.target.value)}
                      className="w-full p-2 bg-slate-700 border border-slate-600 rounded text-white text-sm"
                      disabled={isProcessing}
                    />
                  </div>
                ))}
              </div>
            </div>
            
            <div className="bg-blue-900/20 border border-blue-700 rounded-lg p-4">
              <div className="flex items-start">
                <Calendar className="w-5 h-5 text-blue-400 mr-3 mt-0.5" />
                <div>
                  <h4 className="text-blue-300 font-medium">Automated Monitoring</h4>
                  <p className="text-blue-200 text-sm mt-1">
                    This AOI will be automatically analyzed every week. Each analysis consumes 1 token from your account balance.
                  </p>
                </div>
              </div>
            </div>
          </div>
          
          <div className="p-6 border-t border-slate-700 flex justify-end space-x-3">
            <button
              onClick={handleClose}
              disabled={isProcessing}
              className="px-4 py-2 bg-slate-600 hover:bg-slate-700 disabled:bg-gray-600 text-white rounded transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSubmit}
              disabled={!localName.trim() || isProcessing}
              className="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded font-medium transition-colors flex items-center"
            >
              {isProcessing && <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>}
              {isProcessing ? 'Creating...' : 'Create AOI'}
            </button>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-slate-900">
      {/* Header */}
      <header className="bg-slate-800 border-b border-slate-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center mr-3">
                <Globe className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-white">VANTAGE</h1>
                <p className="text-xs text-gray-400">Satellite Intelligence Platform</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="text-right">
                <div className="text-white font-medium text-sm">
                  {userProfile?.first_name} {userProfile?.last_name}
                </div>
                <div className="text-xs text-gray-400">
                  {userProfile?.tokens_remaining || 0} tokens remaining
                  <br/>DEBUG: {JSON.stringify(userProfile?.tokens_remaining)} | Full: {JSON.stringify(userProfile)}
                </div>
              </div>
              <UserButton afterSignOutUrl="/" />
            </div>
          </div>
        </div>
      </header>

      {/* Navigation - Hidden when in AOI Dashboard */}
      {!showAOIDashboard && (
        <nav className="bg-slate-800 border-b border-slate-700">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex space-x-8">
              {[
                { id: 'overview', label: 'Overview', icon: Activity },
                { id: 'aois', label: 'Areas of Interest', icon: MapPin },
                { id: 'results', label: 'Analysis Results', icon: TrendingUp },
                { id: 'history', label: 'History', icon: BarChart3 },
                { id: 'tokens', label: 'Token Management', icon: Zap }
              ].map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center px-3 py-4 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-400'
                      : 'border-transparent text-gray-400 hover:text-gray-300'
                  }`}
                >
                  <tab.icon className="w-4 h-4 mr-2" />
                  {tab.label}
                </button>
              ))}
            </div>
          </div>
        </nav>
      )}

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        {/* Show AOI Dashboard if selected */}
        {showAOIDashboard ? (
          <AOIDashboardView />
        ) : (
          <>
            {activeTab === 'overview' && (
              <div className="space-y-6">
                <div className="flex justify-between items-center">
                  <h2 className="text-2xl font-bold text-white">System Overview</h2>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                  <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-gray-400 text-sm">Active AOIs</p>
                        <p className="text-2xl font-bold text-white">{aois.length}</p>
                      </div>
                      <MapPin className="w-8 h-8 text-blue-400" />
                    </div>
                  </div>
                  
                  <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-gray-400 text-sm">Total Analyses</p>
                        <p className="text-2xl font-bold text-white">{analysisHistory.length}</p>
                      </div>
                      <BarChart3 className="w-8 h-8 text-green-400" />
                    </div>
                  </div>
                  
                  <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-gray-400 text-sm">Available Tokens</p>
                        <p className="text-2xl font-bold text-white">{userProfile?.tokens_remaining || 0}</p>
                      </div>
                      <Zap className="w-8 h-8 text-yellow-400" />
                    </div>
                  </div>
                  
                  <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-gray-400 text-sm">Tokens Used</p>
                        <p className="text-2xl font-bold text-white">{userProfile?.total_tokens_used || 0}</p>
                      </div>
                      <TrendingUp className="w-8 h-8 text-purple-400" />
                    </div>
                  </div>
                </div>

                <div className="bg-blue-900/20 border border-blue-700 rounded-lg p-6">
                  <h3 className="text-blue-300 font-semibold mb-2 flex items-center">
                    <Calendar className="w-5 h-5 mr-2" />
                    Automated Monitoring System
                  </h3>
                  <p className="text-blue-200 text-sm">
                    All AOIs are automatically analyzed every week. Each analysis consumes 1 token from your account. 
                    Ensure sufficient token balance for continuous monitoring operations.
                  </p>
                </div>
              </div>
            )}

            {activeTab === 'aois' && (
              <div className="space-y-6">
                <div className="flex justify-between items-center">
                  <h2 className="text-2xl font-bold text-white">Areas of Interest</h2>
                  <button
                    onClick={() => setShowCreateAOI(true)}
                    disabled={isProcessing}
                    className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white px-4 py-2 rounded font-medium flex items-center transition-colors"
                  >
                    <Plus className="w-4 h-4 mr-2" />
                    Create AOI
                  </button>
                </div>
                
                {aois.length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {aois.map(aoi => (
                      <AOICard key={aoi.id} aoi={aoi} />
                    ))}
                  </div>
                ) : (
                  <div className="bg-slate-800 border border-slate-700 rounded-lg p-12 text-center">
                    <MapPin className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-white text-lg font-medium mb-2">No Areas of Interest</h3>
                    <p className="text-gray-400 mb-6">Create your first AOI to begin automated satellite monitoring</p>
                    <button
                      onClick={() => setShowCreateAOI(true)}
                      disabled={isProcessing}
                      className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white px-6 py-3 rounded font-medium"
                    >
                      Create First AOI
                    </button>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'results' && (
              <div className="space-y-6">
                <h2 className="text-2xl font-bold text-white">Analysis Results</h2>
                {analysisResults ? (
                  <div className="space-y-6">
                    <div className="bg-green-900/30 border border-green-700 rounded-lg p-4">
                      <div className="flex items-center text-green-400 mb-2">
                        <CheckCircle className="w-5 h-5 mr-2" />
                        <span className="font-semibold">Analysis Complete</span>
                      </div>
                      <p className="text-green-200 text-sm">
                        Satellite imagery analysis completed successfully
                      </p>
                    </div>

                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                      {analysisResults.images?.baseline && (
                        <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
                          <h4 className="text-white font-medium mb-3 flex items-center">
                            <Calendar className="w-4 h-4 mr-2" />
                            Baseline Image
                          </h4>
                          <img 
                            src={`http://localhost:5000${analysisResults.images.baseline.url}`}
                            alt="Baseline Satellite"
                            className="w-full rounded border border-slate-600 mb-3"
                          />
                          <p className="text-gray-300 text-sm">{analysisResults.images.baseline.description}</p>
                        </div>
                      )}

                      {analysisResults.images?.current && (
                        <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
                          <h4 className="text-white font-medium mb-3 flex items-center">
                            <Satellite className="w-4 h-4 mr-2" />
                            Current Image
                          </h4>
                          <img 
                            src={`http://localhost:5000${analysisResults.images.current.url}`}
                            alt="Current Satellite"
                            className="w-full rounded border border-slate-600 mb-3"
                          />
                          <p className="text-gray-300 text-sm">{analysisResults.images.current.description}</p>
                        </div>
                      )}

                      {analysisResults.images?.heatmap && (
                        <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
                          <h4 className="text-white font-medium mb-3 flex items-center">
                            <TrendingUp className="w-4 h-4 mr-2" />
                            Change Detection
                          </h4>
                          <img 
                            src={`http://localhost:5000${analysisResults.images.heatmap.url}`}
                            alt="Change Heatmap"
                            className="w-full rounded border border-slate-600 mb-3"
                          />
                          <p className="text-gray-300 text-sm">{analysisResults.images.heatmap.description}</p>
                        </div>
                      )}
                    </div>

                    <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
                      <h4 className="text-white font-medium mb-4 flex items-center">
                        <BarChart3 className="w-5 h-5 mr-2" />
                        Analysis Summary
                      </h4>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div className="bg-slate-700 p-3 rounded">
                          <div className="text-gray-400">Process ID</div>
                          <div className="text-white font-mono">{analysisResults.process_id}</div>
                        </div>
                        <div className="bg-slate-700 p-3 rounded">
                          <div className="text-gray-400">Change Level</div>
                          <div className="text-white">{analysisResults.change_percentage?.toFixed(2)}%</div>
                        </div>
                        <div className="bg-slate-700 p-3 rounded">
                          <div className="text-gray-400">Tokens Used</div>
                          <div className="text-white">{analysisResults.user_tokens?.tokens_used_this_session || 1}</div>
                        </div>
                        <div className="bg-slate-700 p-3 rounded">
                          <div className="text-gray-400">Status</div>
                          <div className="text-green-400">Completed</div>
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="bg-slate-800 border border-slate-700 rounded-lg p-12 text-center">
                    <TrendingUp className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-white text-lg font-medium mb-2">No Analysis Results</h3>
                    <p className="text-gray-400 mb-6">Run an analysis on an AOI to view results here</p>
                    <button
                      onClick={() => setActiveTab('aois')}
                      className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded font-medium"
                    >
                      View AOIs
                    </button>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'history' && (
              <div className="space-y-6">
                <h2 className="text-2xl font-bold text-white">Analysis History</h2>
                
                <div className="bg-slate-800 border border-slate-700 rounded-lg overflow-hidden">
                  {analysisHistory.length > 0 ? (
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead className="bg-slate-700">
                          <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                              AOI / Analysis
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                              Date & Time
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                              Type
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                              Change
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                              Status
                            </th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-700">
                          {analysisHistory.map(analysis => (
                            <tr key={analysis.id} className="hover:bg-slate-700/50 transition-colors">
                              <td className="px-6 py-4 whitespace-nowrap">
                                <div className="flex items-center">
                                  <div className="w-3 h-3 rounded-full mr-3 bg-blue-500"></div>
                                  <div>
                                    <div className="text-white font-medium">
                                      {analysis.aoi ? analysis.aoi.name : 'Manual Analysis'}
                                    </div>
                                    <div className="text-gray-400 text-sm">
                                      {analysis.aoi?.location_name || 'Default Region'}
                                    </div>
                                  </div>
                                </div>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap">
                                <div className="text-white text-sm">
                                  {new Date(analysis.analysis_timestamp).toLocaleDateString()}
                                </div>
                                <div className="text-gray-400 text-xs">
                                  {new Date(analysis.analysis_timestamp).toLocaleTimeString()}
                                </div>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap">
                                <span className="px-2 py-1 text-xs rounded bg-blue-900 text-blue-300">
                                  {analysis.operation_name || 'Analysis'}
                                </span>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                                {analysis.change_percentage ? `${analysis.change_percentage.toFixed(2)}%` : 'N/A'}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap">
                                <span className="px-2 py-1 text-xs rounded bg-green-900 text-green-300">
                                  {analysis.status || 'completed'}
                                </span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <div className="text-center py-12">
                      <BarChart3 className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                      <h3 className="text-white text-lg font-medium mb-2">No Analysis History</h3>
                      <p className="text-gray-400">Your analysis history will appear here</p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {activeTab === 'tokens' && (
              <div className="space-y-6">
                <h2 className="text-2xl font-bold text-white">Token Management</h2>
                
                <div className="bg-gradient-to-r from-blue-600 to-purple-600 p-6 rounded-lg text-white">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-xl font-semibold">Token Balance</h3>
                      <p className="text-blue-100">Available for AOI monitoring</p>
                    </div>
                    <div className="text-right">
                      <div className="text-4xl font-bold">{userProfile?.tokens_remaining || 0}</div>
                      <div className="text-sm text-blue-200">
                        {userProfile?.total_tokens_used || 0} used total
                      </div>
                    </div>
                  </div>
                  
                  {(userProfile?.tokens_remaining || 0) <= 10 && (
                    <div className="mt-4 p-3 bg-yellow-500/20 rounded border border-yellow-400 text-yellow-100">
                      <AlertTriangle className="w-4 h-4 inline mr-2" />
                      Low token balance - consider purchasing more tokens for continuous monitoring
                    </div>
                  )}
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 text-center">
                    <Zap className="w-8 h-8 text-yellow-400 mx-auto mb-3" />
                    <div className="text-2xl font-bold text-white mb-1">
                      {userProfile?.tokens_remaining || 0}
                    </div>
                    <div className="text-gray-400 text-sm">Available Tokens</div>
                  </div>
                  
                  <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 text-center">
                    <TrendingUp className="w-8 h-8 text-purple-400 mx-auto mb-3" />
                    <div className="text-2xl font-bold text-white mb-1">
                      {userProfile?.total_tokens_used || 0}
                    </div>
                    <div className="text-gray-400 text-sm">Total Consumed</div>
                  </div>
                  
                  <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 text-center">
                    <Calendar className="w-8 h-8 text-green-400 mx-auto mb-3" />
                    <div className="text-2xl font-bold text-white mb-1">
                      {aois.length}
                    </div>
                    <div className="text-gray-400 text-sm">Weekly Consumption</div>
                  </div>
                </div>

                <div className="bg-amber-900/20 border border-amber-700 rounded-lg p-4">
                  <div className="flex items-start">
                    <AlertTriangle className="w-5 h-5 text-amber-400 mr-3 mt-0.5" />
                    <div>
                      <h4 className="text-amber-300 font-medium">Important Notice</h4>
                      <p className="text-amber-200 text-sm mt-1">
                        Insufficient token balance will pause automated monitoring for all AOIs. 
                        Ensure adequate balance to maintain continuous intelligence operations.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </main>

      {showCreateAOI && <CreateAOIModal />}
      
      {isProcessing && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-slate-800 border border-slate-700 p-8 rounded-lg">
            <div className="flex items-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mr-4"></div>
              <span className="text-white text-lg">Processing...</span>
            </div>
          </div>
        </div>
      )}
      
      {/* Debug Component - Remove after fixing */}
      <ApiDebug />
    </div>
  );
};

export default VantageDashboard;