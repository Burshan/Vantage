import React, { useState, useEffect } from 'react';
import { 
  User, CreditCard, Bell, Settings, Globe, Shield, 
  ChevronRight, Check, X, AlertCircle, Info
} from 'lucide-react';
import { useUser } from '@clerk/clerk-react';
import useVantageAPI from '../../hooks/useVantageAPI';
import useToast from '../../hooks/useToast';

const SettingsTab = ({ userProfile }) => {
  const { user } = useUser();
  const { apiCall } = useVantageAPI();
  const toast = useToast();
  
  const [activeSection, setActiveSection] = useState('account');
  const [settings, setSettings] = useState({
    notifications: {
      analysisComplete: true,
      significantChange: true,
      tokenLow: true,
      emailUpdates: false
    },
    analysis: {
      autoRetryFailed: true,
      cloudCoverageThreshold: 50,
      changeThreshold: 5.0,
      defaultAnalysisType: 'baseline_comparison'
    },
    general: {
      dateFormat: 'MM/DD/YYYY'
    }
  });
  const [isSaving, setIsSaving] = useState(false);

  const sections = [
    {
      id: 'account',
      title: 'Account',
      icon: User,
      description: 'Profile and account information'
    },
    {
      id: 'billing',
      title: 'Usage & Tokens',
      icon: CreditCard,
      description: 'Token usage and information'
    },
    {
      id: 'notifications',
      title: 'Notifications',
      icon: Bell,
      description: 'Alert preferences'
    },
    {
      id: 'analysis',
      title: 'Analysis Settings',
      icon: Settings,
      description: 'Default analysis parameters'
    },
    {
      id: 'general',
      title: 'General',
      icon: Globe,
      description: 'Display and format settings'
    }
  ];

  const handleSaveSettings = async () => {
    setIsSaving(true);
    try {
      await apiCall('/api/user/settings', 'POST', { settings });
      toast.showSuccess('Settings saved successfully');
    } catch (error) {
      toast.showError('Failed to save settings');
    } finally {
      setIsSaving(false);
    }
  };

  const updateSetting = (section, key, value) => {
    setSettings(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [key]: value
      }
    }));
  };

  const ToggleSwitch = ({ enabled, onToggle, label, description }) => (
    <div className="flex items-center justify-between py-3">
      <div className="flex-1">
        <div className="text-sm font-medium text-white">{label}</div>
        {description && (
          <div className="text-xs text-gray-400 mt-1">{description}</div>
        )}
      </div>
      <button
        onClick={onToggle}
        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-gray-900 ${
          enabled ? 'bg-blue-600' : 'bg-gray-600'
        }`}
      >
        <span
          className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
            enabled ? 'translate-x-6' : 'translate-x-1'
          }`}
        />
      </button>
    </div>
  );

  const InputField = ({ label, value, onChange, type = 'text', placeholder, description, step }) => (
    <div className="py-3">
      <label className="block text-sm font-medium text-white mb-2">{label}</label>
      {description && (
        <p className="text-xs text-gray-400 mb-2">{description}</p>
      )}
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        step={step}
        className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
      />
    </div>
  );

  const SelectField = ({ label, value, onChange, options, description }) => (
    <div className="py-3">
      <label className="block text-sm font-medium text-white mb-2">{label}</label>
      {description && (
        <p className="text-xs text-gray-400 mb-2">{description}</p>
      )}
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
      >
        {options.map(option => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  );

  const renderAccountSection = () => (
    <div className="space-y-6">
      <div className="flex items-center space-x-4 p-4 bg-gray-800/50 rounded-xl">
        <div className="w-16 h-16 bg-blue-500 rounded-full flex items-center justify-center">
          <User className="w-8 h-8 text-white" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-white">
            {user?.firstName || 'User'} {user?.lastName || ''}
          </h3>
          <p className="text-gray-400">{user?.primaryEmailAddress?.emailAddress}</p>
          <div className="flex items-center space-x-2 mt-2">
            <div className="w-2 h-2 bg-green-400 rounded-full"></div>
            <span className="text-sm text-green-400">Account Active</span>
          </div>
        </div>
      </div>

      <div className="bg-gray-800/30 rounded-xl p-6">
        <h4 className="text-sm font-medium text-gray-300 mb-4">Account Information</h4>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-400">Member since</span>
            <span className="text-white">{new Date(user?.createdAt).toLocaleDateString()}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">User ID</span>
            <span className="text-white font-mono text-xs">{user?.id?.slice(0, 8)}...</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Authentication</span>
            <span className="text-green-400">Clerk SSO</span>
          </div>
        </div>
      </div>
    </div>
  );

  const renderBillingSection = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-gradient-to-br from-blue-900/20 to-blue-800/20 border border-blue-800/30 rounded-xl p-6">
          <div className="flex items-center space-x-3 mb-4">
            <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center">
              <CreditCard className="w-5 h-5 text-white" />
            </div>
            <h4 className="font-medium text-white">Available Tokens</h4>
          </div>
          <div className="text-3xl font-bold text-blue-400 mb-1">
            {userProfile?.tokens_remaining || 0}
          </div>
          <p className="text-xs text-gray-400">Analysis credits remaining</p>
        </div>

        <div className="bg-gray-800/30 rounded-xl p-6">
          <h4 className="font-medium text-white mb-4">Total Usage</h4>
          <div className="text-2xl font-bold text-white mb-1">{userProfile?.total_analyses || 0}</div>
          <p className="text-xs text-gray-400">Analyses completed</p>
        </div>

        <div className="bg-gray-800/30 rounded-xl p-6">
          <h4 className="font-medium text-white mb-4">Account Status</h4>
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-green-400 rounded-full"></div>
            <span className="text-lg font-semibold text-green-400">Active</span>
          </div>
          <p className="text-xs text-gray-400">Token-based usage</p>
        </div>
      </div>

      <div className="bg-gray-800/30 rounded-xl p-6">
        <div className="flex items-center justify-between mb-4">
          <h4 className="font-medium text-white">Token Information</h4>
        </div>
        <div className="space-y-3">
          <div className="flex items-center justify-between py-2">
            <div>
              <span className="text-white text-sm">Tokens Remaining</span>
            </div>
            <span className="text-green-400 text-sm font-semibold">{userProfile?.tokens_remaining || 0}</span>
          </div>
          <div className="flex items-center justify-between py-2 border-t border-gray-700/50">
            <div>
              <span className="text-white text-sm">Cost per Analysis</span>
            </div>
            <span className="text-gray-300 text-sm">1 token</span>
          </div>
          <div className="flex items-center justify-between py-2 border-t border-gray-700/50">
            <div>
              <span className="text-white text-sm">Cost per AOI Creation</span>
            </div>
            <span className="text-gray-300 text-sm">1 token</span>
          </div>
        </div>
      </div>
    </div>
  );

  const renderNotificationsSection = () => (
    <div className="space-y-6">
      <div className="bg-gray-800/30 rounded-xl p-6">
        <h4 className="font-medium text-white mb-6">Analysis Notifications</h4>
        <div className="space-y-1">
          <ToggleSwitch
            enabled={settings.notifications.analysisComplete}
            onToggle={() => updateSetting('notifications', 'analysisComplete', !settings.notifications.analysisComplete)}
            label="Analysis Complete"
            description="Get notified when your analysis is ready"
          />
          <ToggleSwitch
            enabled={settings.notifications.significantChange}
            onToggle={() => updateSetting('notifications', 'significantChange', !settings.notifications.significantChange)}
            label="Significant Changes"
            description="Alert when major changes are detected"
          />
        </div>
      </div>

      <div className="bg-gray-800/30 rounded-xl p-6">
        <h4 className="font-medium text-white mb-6">Account Notifications</h4>
        <div className="space-y-1">
          <ToggleSwitch
            enabled={settings.notifications.tokenLow}
            onToggle={() => updateSetting('notifications', 'tokenLow', !settings.notifications.tokenLow)}
            label="Low Token Alert"
            description="Notify when you have less than 10 tokens"
          />
          <ToggleSwitch
            enabled={settings.notifications.emailUpdates}
            onToggle={() => updateSetting('notifications', 'emailUpdates', !settings.notifications.emailUpdates)}
            label="Email Updates"
            description="Receive product updates via email"
          />
        </div>
      </div>
    </div>
  );

  const renderAnalysisSection = () => (
    <div className="space-y-6">
      <div className="bg-gray-800/30 rounded-xl p-6">
        <h4 className="font-medium text-white mb-6">Default Analysis Settings</h4>
        <div className="space-y-4">
          <SelectField
            label="Default Analysis Type"
            value={settings.analysis.defaultAnalysisType}
            onChange={(value) => updateSetting('analysis', 'defaultAnalysisType', value)}
            options={[
              { value: 'baseline_comparison', label: 'Baseline Comparison' },
              { value: 'temporal_analysis', label: 'Temporal Analysis' },
              { value: 'change_detection', label: 'Change Detection' }
            ]}
            description="The analysis type used by default for new analyses"
          />
          
          <InputField
            label="Cloud Coverage Threshold (%)"
            type="number"
            value={settings.analysis.cloudCoverageThreshold}
            onChange={(value) => updateSetting('analysis', 'cloudCoverageThreshold', parseInt(value))}
            placeholder="50"
            description="Skip analysis if cloud coverage exceeds this percentage"
          />
          
          <InputField
            label="Change Detection Threshold (%)"
            type="number"
            step="0.1"
            value={settings.analysis.changeThreshold}
            onChange={(value) => updateSetting('analysis', 'changeThreshold', parseFloat(value))}
            placeholder="5.0"
            description="Minimum change percentage to consider significant"
          />
        </div>
      </div>

      <div className="bg-gray-800/30 rounded-xl p-6">
        <h4 className="font-medium text-white mb-6">Processing Options</h4>
        <ToggleSwitch
          enabled={settings.analysis.autoRetryFailed}
          onToggle={() => updateSetting('analysis', 'autoRetryFailed', !settings.analysis.autoRetryFailed)}
          label="Auto-retry Failed Analyses"
          description="Automatically retry failed analyses after 1 hour"
        />
      </div>
    </div>
  );

  const renderGeneralSection = () => (
    <div className="space-y-6">
      <div className="bg-gray-800/30 rounded-xl p-6">
        <h4 className="font-medium text-white mb-6">Display Settings</h4>
        <div className="space-y-4">
          <SelectField
            label="Date Format"
            value={settings.general.dateFormat}
            onChange={(value) => updateSetting('general', 'dateFormat', value)}
            options={[
              { value: 'MM/DD/YYYY', label: 'MM/DD/YYYY (US)' },
              { value: 'DD/MM/YYYY', label: 'DD/MM/YYYY (EU)' },
              { value: 'YYYY-MM-DD', label: 'YYYY-MM-DD (ISO)' }
            ]}
            description="Choose how dates are displayed throughout the application"
          />
        </div>
      </div>

      <div className="bg-gray-800/30 rounded-xl p-6">
        <h4 className="font-medium text-white mb-4">Application Info</h4>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-400">Version</span>
            <span className="text-white">v2.1.0</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Theme</span>
            <span className="text-white">Dark (Fixed)</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Image Processing</span>
            <span className="text-white">OpenCV Enhanced</span>
          </div>
        </div>
      </div>
    </div>
  );

  const renderContent = () => {
    switch (activeSection) {
      case 'account': return renderAccountSection();
      case 'billing': return renderBillingSection();
      case 'notifications': return renderNotificationsSection();
      case 'analysis': return renderAnalysisSection();
      case 'general': return renderGeneralSection();
      default: return renderAccountSection();
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">Settings</h1>
          <p className="text-gray-400">Manage your account, preferences, and application settings</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Settings Navigation */}
          <div className="lg:col-span-1">
            <div className="bg-gray-800/30 rounded-xl p-4">
              <nav className="space-y-1">
                {sections.map((section) => (
                  <button
                    key={section.id}
                    onClick={() => setActiveSection(section.id)}
                    className={`w-full flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-all duration-200 group ${
                      activeSection === section.id
                        ? 'bg-blue-600 text-white shadow-lg'
                        : 'text-gray-300 hover:text-white hover:bg-gray-700/50'
                    }`}
                  >
                    <section.icon className="w-5 h-5 mr-3 flex-shrink-0" />
                    <div className="flex-1 text-left">
                      <div className="font-medium">{section.title}</div>
                      <div className="text-xs opacity-80">{section.description}</div>
                    </div>
                    <ChevronRight className={`w-4 h-4 ml-2 transition-transform ${
                      activeSection === section.id ? 'rotate-90' : 'group-hover:translate-x-1'
                    }`} />
                  </button>
                ))}
              </nav>
            </div>
          </div>

          {/* Settings Content */}
          <div className="lg:col-span-3">
            <div className="bg-gray-800/20 rounded-xl p-6">
              {renderContent()}
              
              {/* Save Button */}
              {activeSection !== 'account' && activeSection !== 'billing' && (
                <div className="flex justify-end pt-6 mt-6 border-t border-gray-700/50">
                  <button
                    onClick={handleSaveSettings}
                    disabled={isSaving}
                    className="flex items-center px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 text-white font-medium rounded-lg transition-colors duration-200"
                  >
                    {isSaving ? (
                      <>
                        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                        Saving...
                      </>
                    ) : (
                      <>
                        <Check className="w-4 h-4 mr-2" />
                        Save Changes
                      </>
                    )}
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsTab;