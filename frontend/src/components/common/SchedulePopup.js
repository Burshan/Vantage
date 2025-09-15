import React, { useState, useEffect } from 'react';
import { Calendar, Clock, Save, X, AlertTriangle } from 'lucide-react';

const SchedulePopup = ({ isOpen, onClose, onSave, aoiId, currentSchedule = null }) => {
  const [scheduleData, setScheduleData] = useState({
    date: '',
    time: '',
    frequency: 'once', // 'once', 'daily', 'weekly', 'monthly'
    enabled: true
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (currentSchedule) {
      const scheduleDate = new Date(currentSchedule.next_run_at);
      setScheduleData({
        date: scheduleDate.toISOString().split('T')[0],
        time: scheduleDate.toTimeString().substr(0, 5),
        frequency: currentSchedule.monitoring_frequency || 'once',
        enabled: currentSchedule.is_active
      });
    } else {
      // Default to tomorrow at current time
      const tomorrow = new Date();
      tomorrow.setDate(tomorrow.getDate() + 1);
      setScheduleData({
        date: tomorrow.toISOString().split('T')[0],
        time: new Date().toTimeString().substr(0, 5),
        frequency: 'once',
        enabled: true
      });
    }
  }, [currentSchedule, isOpen]);

  const handleSave = async () => {
    // Prevent double-clicking
    if (isLoading) return;
    
    if (!scheduleData.date || !scheduleData.time) {
      setError('Please select both date and time');
      return;
    }

    // Create the datetime in user's local timezone, then convert to UTC for backend
    const [year, month, day] = scheduleData.date.split('-').map(Number);
    const [hours, minutes] = scheduleData.time.split(':').map(Number);
    
    // Create local datetime first
    const localDateTime = new Date(year, month - 1, day, hours, minutes);
    
    // Convert to UTC for backend (this preserves the user's intended local time)
    const scheduleDateTime = new Date(localDateTime.getTime() - (localDateTime.getTimezoneOffset() * 60000));
    if (scheduleDateTime <= new Date()) {
      setError('Please select a future date and time');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      const payload = {
        frequency: scheduleData.frequency,
        scheduled_at: scheduleDateTime.toISOString(),
        enabled: scheduleData.enabled
      };

      console.log('🚀 SchedulePopup sending payload:', payload);
      console.log('📅 Schedule date/time:', scheduleDateTime);
      console.log('🎯 Target AOI ID:', aoiId);

      await onSave(aoiId, payload);
      
      console.log('✅ Schedule save completed successfully');
      onClose();
    } catch (err) {
      console.error('❌ SchedulePopup save error:', err);
      setError(err.message || 'Failed to save schedule');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRemoveSchedule = async () => {
    if (!window.confirm('Remove scheduled analysis?')) return;
    
    setIsLoading(true);
    try {
      await onSave(aoiId, { 
        enabled: false,
        frequency: 'none' // Explicitly indicate we're removing the schedule
      });
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to remove schedule');
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-slate-800 rounded-lg border border-slate-700 p-6 w-full max-w-md mx-4">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center">
            <Calendar className="w-5 h-5 text-blue-400 mr-2" />
            <h3 className="text-lg font-semibold text-white">
              {currentSchedule ? 'Update Schedule' : 'Schedule Analysis'}
            </h3>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-900/50 border border-red-700 rounded flex items-center">
            <AlertTriangle className="w-4 h-4 text-red-400 mr-2 flex-shrink-0" />
            <span className="text-red-300 text-sm">{error}</span>
          </div>
        )}

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Date
            </label>
            <input
              type="date"
              value={scheduleData.date}
              onChange={(e) => setScheduleData(prev => ({ ...prev, date: e.target.value }))}
              className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              min={new Date().toISOString().split('T')[0]}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Time (Your local time)
            </label>
            <div className="relative">
              <Clock className="absolute left-3 top-2.5 w-4 h-4 text-gray-400" />
              <input
                type="time"
                value={scheduleData.time}
                onChange={(e) => setScheduleData(prev => ({ ...prev, time: e.target.value }))}
                className="w-full pl-10 pr-3 py-2 bg-slate-700 border border-slate-600 rounded text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Frequency
            </label>
            <select
              value={scheduleData.frequency}
              onChange={(e) => setScheduleData(prev => ({ ...prev, frequency: e.target.value }))}
              className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="once">Run once</option>
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
            </select>
          </div>

          {currentSchedule && (
            <div className="flex items-center">
              <input
                type="checkbox"
                id="enabled"
                checked={scheduleData.enabled}
                onChange={(e) => setScheduleData(prev => ({ ...prev, enabled: e.target.checked }))}
                className="mr-2 rounded bg-slate-700 border-slate-600"
              />
              <label htmlFor="enabled" className="text-sm text-gray-300">
                Keep schedule active
              </label>
            </div>
          )}
        </div>

        <div className="flex gap-3 mt-6">
          <button
            onClick={handleSave}
            disabled={isLoading}
            className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 disabled:cursor-not-allowed text-white font-medium py-2 px-4 rounded transition-colors flex items-center justify-center"
          >
            <Save className="w-4 h-4 mr-2" />
            {isLoading ? 'Saving...' : 'Save Schedule'}
          </button>
          
          {currentSchedule && (
            <button
              onClick={handleRemoveSchedule}
              disabled={isLoading}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-red-800 text-white rounded transition-colors"
            >
              Remove
            </button>
          )}
          
          <button
            onClick={onClose}
            disabled={isLoading}
            className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded transition-colors"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
};

export default SchedulePopup;