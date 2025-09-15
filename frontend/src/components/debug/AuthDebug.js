import React, { useState } from 'react';
import { useAuth } from '@clerk/clerk-react';
import useVantageAPI from '../../hooks/useVantageAPI';

const AuthDebug = () => {
  const { getToken, userId } = useAuth();
  const { apiCall } = useVantageAPI();
  const [testResult, setTestResult] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const testAuth = async () => {
    setIsLoading(true);
    setTestResult('Testing...');
    
    try {
      // Test token retrieval
      const token = await getToken({ skipCache: true });
      console.log('Token retrieved:', token ? '✅ Success' : '❌ Failed');
      
      // Test API call
      const data = await apiCall('/api/user/profile');
      console.log('API call result:', data);
      
      setTestResult(`✅ Authentication working!\nUser ID: ${userId}\nToken: ${token ? 'Present' : 'Missing'}\nAPI Response: ${JSON.stringify(data.user, null, 2)}`);
      
    } catch (error) {
      console.error('Auth test failed:', error);
      setTestResult(`❌ Authentication failed: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const testScheduleAPI = async () => {
    setIsLoading(true);
    setTestResult('Testing schedule API...');
    
    try {
      // Test with a real AOI ID (you might need to adjust this)
      const data = await apiCall('/api/aoi/14/schedule-monitoring');
      setTestResult(`✅ Schedule API working!\nResponse: ${JSON.stringify(data, null, 2)}`);
    } catch (error) {
      setTestResult(`❌ Schedule API failed: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed bottom-4 right-4 bg-slate-800 border border-slate-600 rounded-lg p-4 max-w-md">
      <h3 className="text-white font-semibold mb-3">🐛 Auth Debug</h3>
      
      <div className="space-y-2 mb-4">
        <button
          onClick={testAuth}
          disabled={isLoading}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white px-3 py-2 rounded text-sm"
        >
          Test Authentication
        </button>
        
        <button
          onClick={testScheduleAPI}
          disabled={isLoading}
          className="w-full bg-purple-600 hover:bg-purple-700 text-white px-3 py-2 rounded text-sm"
        >
          Test Schedule API
        </button>
      </div>

      {testResult && (
        <div className="bg-slate-700 rounded p-3 max-h-48 overflow-y-auto">
          <pre className="text-xs text-gray-300 whitespace-pre-wrap">
            {testResult}
          </pre>
        </div>
      )}
    </div>
  );
};

export default AuthDebug;