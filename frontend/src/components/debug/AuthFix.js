import React, { useState } from 'react';
import { useAuth } from '@clerk/clerk-react';
import useVantageAPI from '../../hooks/useVantageAPI';

const AuthFix = () => {
  const { getToken, userId, isSignedIn } = useAuth();
  const { apiCall } = useVantageAPI();
  const [status, setStatus] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const testAuth = async () => {
    setIsLoading(true);
    setStatus('Testing...');
    
    try {
      console.log('🔍 Auth Debug Test Starting...');
      
      // Step 1: Check Clerk auth status
      console.log('📋 Clerk Status:', { isSignedIn, userId });
      
      // Step 2: Try to get token
      const token = await getToken({ skipCache: true });
      console.log('🎟️ Token:', token ? 'Present' : 'Missing');
      
      if (!token) {
        setStatus('❌ No token available from Clerk');
        return;
      }
      
      // Step 3: Test API call
      const result = await apiCall('/api/user/profile');
      console.log('✅ API Test Result:', result);
      
      setStatus(`✅ Auth working! User: ${result.user?.email || 'Unknown'}`);
      
    } catch (error) {
      console.error('❌ Auth test failed:', error);
      setStatus(`❌ Auth failed: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const testScheduleAPI = async () => {
    setIsLoading(true);
    setStatus('Testing schedule API...');
    
    try {
      const result = await apiCall('/api/aoi/14/schedule-monitoring');
      console.log('📅 Schedule API Result:', result);
      setStatus(`✅ Schedule API working! Has schedule: ${result.has_schedule}`);
    } catch (error) {
      console.error('❌ Schedule API failed:', error);
      setStatus(`❌ Schedule API failed: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const forceTokenRefresh = async () => {
    setIsLoading(true);
    setStatus('Refreshing token...');
    
    try {
      // Force refresh token
      const newToken = await getToken({ skipCache: true });
      console.log('🔄 Force refreshed token:', newToken ? 'Success' : 'Failed');
      setStatus(`🔄 Token refreshed: ${newToken ? 'Success' : 'Failed'}`);
    } catch (error) {
      setStatus(`❌ Refresh failed: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed top-4 left-4 bg-slate-800 border border-slate-600 rounded-lg p-4 min-w-72">
      <h3 className="text-white font-semibold mb-3">🔐 Auth Debug & Fix</h3>
      
      <div className="text-xs text-gray-300 mb-3">
        <div>Signed In: {isSignedIn ? '✅' : '❌'}</div>
        <div>User ID: {userId || 'None'}</div>
      </div>
      
      <div className="space-y-2 mb-4">
        <button
          onClick={testAuth}
          disabled={isLoading}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm"
        >
          Test Auth
        </button>
        
        <button
          onClick={testScheduleAPI}
          disabled={isLoading}
          className="w-full bg-purple-600 hover:bg-purple-700 text-white px-3 py-1 rounded text-sm"
        >
          Test Schedule API
        </button>
        
        <button
          onClick={forceTokenRefresh}
          disabled={isLoading}
          className="w-full bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-sm"
        >
          Force Token Refresh
        </button>
      </div>

      {status && (
        <div className="bg-slate-700 rounded p-2">
          <pre className="text-xs text-gray-300 whitespace-pre-wrap">
            {status}
          </pre>
        </div>
      )}
    </div>
  );
};

export default AuthFix;