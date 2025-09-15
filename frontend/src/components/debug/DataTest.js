import React, { useState, useEffect } from 'react';
import { useAuth } from '@clerk/clerk-react';
import { API_BASE_URL } from '../../config/api';

const DataTest = () => {
  const { getToken } = useAuth();
  const [testResults, setTestResults] = useState({
    userProfile: null,
    aois: null,
    history: null,
    rawResponses: {
      userProfile: null,
      aois: null,
      history: null
    }
  });

  const apiCall = async (endpoint) => {
    const token = await getToken({ skipCache: true });
    if (!token) throw new Error('No auth token from Clerk');

    const res = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      mode: 'cors',
    });

    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }

    return await res.json();
  };

  const testAPI = async () => {
    console.log('🧪 Starting API tests...');
    
    try {
      // Test user profile
      console.log('1️⃣ Testing user profile...');
      const userResponse = await apiCall('/api/user/profile');
      console.log('👤 User response:', userResponse);
      
      // Test AOIs
      console.log('2️⃣ Testing AOIs...');
      const aoiResponse = await apiCall('/api/aoi');
      console.log('🗺️ AOI response:', aoiResponse);
      
      // Test history
      console.log('3️⃣ Testing history...');
      const historyResponse = await apiCall('/api/user/history?limit=5');
      console.log('📊 History response:', historyResponse);

      // Process responses
      const processedData = {
        userProfile: userResponse.data?.user || userResponse.user || userResponse,
        aois: aoiResponse.data?.areas_of_interest || aoiResponse.areas_of_interest || aoiResponse,
        history: historyResponse.data?.history || historyResponse.history || historyResponse,
        rawResponses: {
          userProfile: userResponse,
          aois: aoiResponse,
          history: historyResponse
        }
      };

      console.log('✅ Processed data:', processedData);
      setTestResults(processedData);
      
    } catch (error) {
      console.error('❌ API test failed:', error);
      setTestResults(prev => ({ ...prev, error: error.message }));
    }
  };

  useEffect(() => {
    testAPI();
  }, []);

  return (
    <div className="fixed bottom-4 right-4 bg-slate-800 border border-slate-600 rounded-lg p-4 max-w-md max-h-96 overflow-y-auto z-50">
      <h3 className="text-white font-semibold mb-3">🧪 Data Test Debug</h3>
      
      <div className="space-y-2 text-xs text-gray-300">
        <div>
          <strong>👤 User Profile:</strong>
          <div className="ml-2">
            ID: {testResults.userProfile?.id || 'null'}<br/>
            Tokens: {testResults.userProfile?.tokens_remaining ?? 'null'}<br/>
            Email: {testResults.userProfile?.email || 'null'}
          </div>
        </div>
        
        <div>
          <strong>🗺️ AOIs:</strong>
          <div className="ml-2">
            Count: {Array.isArray(testResults.aois) ? testResults.aois.length : 'null'}<br/>
            First: {testResults.aois?.[0]?.name || 'none'}
          </div>
        </div>
        
        <div>
          <strong>📊 History:</strong>
          <div className="ml-2">
            Count: {Array.isArray(testResults.history) ? testResults.history.length : 'null'}<br/>
            First: {testResults.history?.[0]?.operation_name || 'none'}
          </div>
        </div>

        {testResults.error && (
          <div className="text-red-400">
            <strong>❌ Error:</strong> {testResults.error}
          </div>
        )}
        
        <div className="mt-4 pt-2 border-t border-slate-600">
          <strong>📋 Raw Response Types:</strong>
          <div className="ml-2">
            User: {typeof testResults.rawResponses.userProfile}<br/>
            AOI: {typeof testResults.rawResponses.aois}<br/>
            History: {typeof testResults.rawResponses.history}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DataTest;