import React, { useState, useEffect } from 'react';
import useVantageAPI from '../../hooks/useVantageAPI';

const ScheduleDebug = () => {
  const { apiCall } = useVantageAPI();
  const [scheduleData, setScheduleData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [testResult, setTestResult] = useState('');

  const testAoiId = 14; // Use the AOI ID from your logs

  const loadSchedule = async () => {
    setIsLoading(true);
    try {
      const data = await apiCall(`/api/aoi/${testAoiId}/schedule-monitoring`);
      setScheduleData(data);
      setTestResult(`✅ Schedule loaded:\n${JSON.stringify(data, null, 2)}`);
    } catch (error) {
      setTestResult(`❌ Failed to load schedule: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const createTestSchedule = async () => {
    setIsLoading(true);
    try {
      const tomorrow = new Date();
      tomorrow.setDate(tomorrow.getDate() + 1);
      tomorrow.setHours(14, 0, 0, 0); // 2 PM tomorrow
      
      const payload = {
        frequency: 'once',
        scheduled_at: tomorrow.toISOString(),
        enabled: true
      };

      const data = await apiCall(`/api/aoi/${testAoiId}/schedule-monitoring`, {
        method: 'POST',
        body: JSON.stringify(payload)
      });
      
      setTestResult(`✅ Schedule created:\n${JSON.stringify(data, null, 2)}`);
      await loadSchedule();
    } catch (error) {
      setTestResult(`❌ Failed to create schedule: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const removeSchedule = async () => {
    setIsLoading(true);
    try {
      const payload = {
        frequency: 'none',
        enabled: false
      };

      const data = await apiCall(`/api/aoi/${testAoiId}/schedule-monitoring`, {
        method: 'POST',
        body: JSON.stringify(payload)
      });
      
      setTestResult(`✅ Schedule removed:\n${JSON.stringify(data, null, 2)}`);
      await loadSchedule();
    } catch (error) {
      setTestResult(`❌ Failed to remove schedule: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadSchedule();
  }, []);

  return (
    <div className="fixed top-4 right-4 bg-slate-800 border border-slate-600 rounded-lg p-4 max-w-md max-h-96 overflow-y-auto">
      <h3 className="text-white font-semibold mb-3">🗓️ Schedule Debug</h3>
      
      <div className="space-y-2 mb-4">
        <button
          onClick={loadSchedule}
          disabled={isLoading}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white px-3 py-2 rounded text-sm"
        >
          {isLoading ? 'Loading...' : 'Reload Schedule'}
        </button>
        
        <button
          onClick={createTestSchedule}
          disabled={isLoading}
          className="w-full bg-green-600 hover:bg-green-700 text-white px-3 py-2 rounded text-sm"
        >
          Create Test Schedule
        </button>
        
        <button
          onClick={removeSchedule}
          disabled={isLoading}
          className="w-full bg-red-600 hover:bg-red-700 text-white px-3 py-2 rounded text-sm"
        >
          Remove Schedule
        </button>
      </div>

      <div className="text-xs text-gray-300 mb-2">
        <strong>Current URL:</strong> {window.location.href}
      </div>

      {scheduleData && (
        <div className="mb-4 p-2 bg-slate-700 rounded">
          <div className="text-xs text-gray-300">
            <strong>Has Schedule:</strong> {scheduleData.has_schedule ? '✅ Yes' : '❌ No'}
          </div>
          {scheduleData.has_schedule && (
            <div className="text-xs text-gray-300">
              <strong>Next Run:</strong> {scheduleData.next_run_at ? new Date(scheduleData.next_run_at).toLocaleString() : 'None'}
            </div>
          )}
        </div>
      )}

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

export default ScheduleDebug;