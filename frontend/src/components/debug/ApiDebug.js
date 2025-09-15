import React, { useState, useEffect } from 'react';
import useVantageAPI from '../../hooks/useVantageAPI';

const ApiDebug = () => {
  const { apiCall } = useVantageAPI();
  const [debugData, setDebugData] = useState({});
  const [error, setError] = useState(null);
  
  const testAPIs = async () => {
    try {
      console.log('🔬 ApiDebug: Testing all APIs...');
      
      // Test user profile
      const profileResponse = await apiCall('/api/user/profile');
      console.log('🔬 ApiDebug Profile Response:', profileResponse);
      
      // Test AOIs  
      const aoiResponse = await apiCall('/api/aoi');
      console.log('🔬 ApiDebug AOI Response:', aoiResponse);
      
      // Test history
      const historyResponse = await apiCall('/api/user/history?limit=5');
      console.log('🔬 ApiDebug History Response:', historyResponse);
      
      setDebugData({
        profile: profileResponse,
        aoi: aoiResponse,
        history: historyResponse,
        // Parsed data
        userData: profileResponse.data?.user || profileResponse.user || profileResponse,
        aoiData: aoiResponse.data?.areas_of_interest || aoiResponse.areas_of_interest || aoiResponse,
        historyData: historyResponse.data?.history || historyResponse.history || historyResponse
      });
      
    } catch (err) {
      console.error('🔬 ApiDebug Error:', err);
      setError(err.message);
    }
  };
  
  useEffect(() => {
    testAPIs();
  }, []);
  
  return (
    <div className="fixed top-4 left-4 bg-black border border-red-500 rounded-lg p-4 max-w-md max-h-96 overflow-y-auto z-50 text-white">
      <h3 className="text-red-400 font-bold mb-3">🔬 API Debug Panel</h3>
      
      {error && (
        <div className="text-red-400 mb-3">
          <strong>Error:</strong> {error}
        </div>
      )}
      
      <div className="space-y-2 text-xs">
        <div>
          <strong className="text-green-400">👤 User Tokens:</strong>
          <div className="ml-2">
            Raw: {debugData.userData?.tokens_remaining || 'null'}<br/>
            Type: {typeof debugData.userData?.tokens_remaining}<br/>
            ID: {debugData.userData?.id || 'null'}
          </div>
        </div>
        
        <div>
          <strong className="text-blue-400">🗺️ AOI Count:</strong>
          <div className="ml-2">
            Raw: {Array.isArray(debugData.aoiData) ? debugData.aoiData.length : 'null'}<br/>
            Type: {typeof debugData.aoiData}<br/>
            IsArray: {Array.isArray(debugData.aoiData) ? 'true' : 'false'}
          </div>
        </div>
        
        <div>
          <strong className="text-purple-400">📊 History Count:</strong>
          <div className="ml-2">
            Raw: {Array.isArray(debugData.historyData) ? debugData.historyData.length : 'null'}<br/>
            Type: {typeof debugData.historyData}<br/>
            IsArray: {Array.isArray(debugData.historyData) ? 'true' : 'false'}
          </div>
        </div>
        
        <div className="mt-4 pt-2 border-t border-gray-600">
          <strong className="text-yellow-400">📋 Raw Response Sample:</strong>
          <div className="ml-2 text-xs bg-gray-900 p-2 rounded mt-1">
            Profile Success: {debugData.profile?.success ? 'true' : 'false'}<br/>
            Profile Data Keys: {debugData.profile?.data ? Object.keys(debugData.profile.data).join(', ') : 'none'}
          </div>
        </div>
      </div>
      
      <button 
        onClick={testAPIs}
        className="mt-3 px-2 py-1 bg-red-600 hover:bg-red-700 text-white text-xs rounded"
      >
        🔄 Refresh APIs
      </button>
    </div>
  );
};

export default ApiDebug;