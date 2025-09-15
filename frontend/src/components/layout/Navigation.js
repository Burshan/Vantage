import React, { useState } from 'react';
import { 
  Activity, MapPin, TrendingUp, BarChart3, Zap, 
  Settings, Bell, HelpCircle, User, LogOut, 
  ChevronLeft, ChevronRight, Satellite, 
  Shield, CreditCard, Database, LifeBuoy,
  Menu, X
} from 'lucide-react';
import { useAuth } from '@clerk/clerk-react';

const Navigation = ({ activeTab, onTabChange, isInAOIDashboard = false, userProfile }) => {
  const { signOut, user } = useAuth();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Check if user is admin based on database role
  const isAdmin = userProfile?.is_admin === true || 
                  userProfile?.role === 'admin' || 
                  userProfile?.role === 'super_admin';

  const navigationTabs = [
    { id: 'overview', label: 'Overview', icon: Activity, description: 'Dashboard overview' },
    { id: 'aois', label: 'Areas of Interest', icon: MapPin, description: 'Manage monitoring areas' },
    { id: 'results', label: 'Analysis Results', icon: TrendingUp, description: 'View analysis results' },
    { id: 'history', label: 'History', icon: BarChart3, description: 'Analysis history' },
    { id: 'tokens', label: 'Token Management', icon: Zap, description: 'Manage API tokens' },
    { id: 'settings', label: 'Settings', icon: Settings, description: 'Account & preferences' },
    { id: 'admin', label: 'Admin Panel', icon: Shield, description: 'System administration', adminOnly: true }
  ];

  const accountItems = [
    { id: 'profile', label: 'Profile', icon: User, description: 'Account settings' },
    { id: 'billing', label: 'Billing', icon: CreditCard, description: 'Subscription & billing' },
    { id: 'api', label: 'API Keys', icon: Database, description: 'Developer access' },
  ];

  const supportItems = [
    { id: 'help', label: 'Help Center', icon: HelpCircle, description: 'Documentation & guides' },
    { id: 'support', label: 'Contact Support', icon: LifeBuoy, description: '24/7 customer support' },
  ];

  const SidebarContent = ({ isMobile = false }) => (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-6 border-b border-slate-700/50">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center shadow-lg">
              <Satellite className="w-6 h-6 text-white" />
            </div>
            {(!sidebarCollapsed || isMobile) && (
              <div>
                <h1 className="text-xl font-bold bg-gradient-to-r from-white to-blue-100 bg-clip-text text-transparent">
                  Vantage
                </h1>
                <p className="text-xs text-gray-400 font-medium tracking-wide">
                  Satellite Intelligence Platform
                </p>
              </div>
            )}
          </div>
          {!isMobile && (
            <button
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
              className="p-1 text-gray-400 hover:text-white rounded"
            >
              {sidebarCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
            </button>
          )}
          {isMobile && (
            <button
              onClick={() => setMobileMenuOpen(false)}
              className="p-1 text-gray-400 hover:text-white rounded"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>
      </div>

      {/* Status Bar */}
      <div className="p-4 border-b border-slate-700/50">
        {(!sidebarCollapsed || isMobile) && (
          <div className="bg-gradient-to-r from-green-900/20 to-blue-900/20 border border-green-800/30 rounded-xl p-3">
            <div className="flex items-center space-x-2 mb-2">
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
              <span className="text-xs font-semibold text-green-300 uppercase tracking-wide">System Online</span>
            </div>
            <div className="text-xs text-gray-400">
              All satellite services operational
            </div>
          </div>
        )}
      </div>

      {/* Main Navigation */}
      <div className="flex-1 px-3 py-4">
        {/* Main Tabs */}
        <div className="mb-8">
          {(!sidebarCollapsed || isMobile) && (
            <h3 className="px-3 text-xs font-bold text-gray-400 uppercase tracking-widest mb-4 flex items-center">
              <div className="w-4 h-px bg-gradient-to-r from-gray-400 to-transparent mr-2"></div>
              Navigation
            </h3>
          )}
          <nav className="space-y-2">
            {navigationTabs.filter(tab => !tab.adminOnly || isAdmin).map(tab => (
              <button
                key={tab.id}
                onClick={() => onTabChange(tab.id)}
                className={`w-full flex items-center px-4 py-3 text-sm font-medium rounded-xl transition-all duration-200 ${
                  activeTab === tab.id && !isInAOIDashboard
                    ? 'bg-gradient-to-r from-blue-600 to-blue-500 text-white shadow-lg shadow-blue-600/25 border border-blue-400/20'
                    : 'text-gray-300 hover:text-white hover:bg-slate-700/50 hover:border-slate-600/50 border border-transparent'
                } ${tab.adminOnly ? 'border-red-800/30 bg-red-900/10' : ''}`}
                title={sidebarCollapsed ? tab.label : ''}
              >
                <tab.icon className="w-5 h-5 flex-shrink-0" />
                {(!sidebarCollapsed || isMobile) && (
                  <>
                    <span className="ml-3 truncate font-medium">{tab.label}</span>
                    {tab.adminOnly && (
                      <span className="ml-2 px-1.5 py-0.5 bg-red-600 text-xs rounded text-white">ADMIN</span>
                    )}
                    {activeTab === tab.id && !isInAOIDashboard && (
                      <div className="ml-auto w-2 h-2 bg-white rounded-full"></div>
                    )}
                  </>
                )}
              </button>
            ))}
          </nav>
        </div>

        {/* Account Section */}
        <div className="mb-8">
          {(!sidebarCollapsed || isMobile) && (
            <h3 className="px-3 text-xs font-bold text-gray-400 uppercase tracking-widest mb-4 flex items-center">
              <div className="w-4 h-px bg-gradient-to-r from-gray-400 to-transparent mr-2"></div>
              Account
            </h3>
          )}
          <nav className="space-y-1">
            {accountItems.map(item => (
              <button
                key={item.id}
                className="w-full flex items-center px-4 py-2.5 text-sm font-medium text-gray-300 hover:text-white hover:bg-slate-700/40 rounded-lg transition-all duration-200 group"
                title={sidebarCollapsed ? item.label : ''}
              >
                <item.icon className="w-4 h-4 flex-shrink-0 group-hover:scale-110 transition-transform duration-200" />
                {(!sidebarCollapsed || isMobile) && (
                  <span className="ml-3 truncate">{item.label}</span>
                )}
              </button>
            ))}
          </nav>
        </div>

        {/* Support Section */}
        <div>
          {(!sidebarCollapsed || isMobile) && (
            <h3 className="px-3 text-xs font-bold text-gray-400 uppercase tracking-widest mb-4 flex items-center">
              <div className="w-4 h-px bg-gradient-to-r from-gray-400 to-transparent mr-2"></div>
              Support
            </h3>
          )}
          <nav className="space-y-1">
            {supportItems.map(item => (
              <button
                key={item.id}
                className="w-full flex items-center px-4 py-2.5 text-sm font-medium text-gray-300 hover:text-white hover:bg-slate-700/40 rounded-lg transition-all duration-200 group"
                title={sidebarCollapsed ? item.label : ''}
              >
                <item.icon className="w-4 h-4 flex-shrink-0 group-hover:scale-110 transition-transform duration-200" />
                {(!sidebarCollapsed || isMobile) && (
                  <span className="ml-3 truncate">{item.label}</span>
                )}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Footer Actions */}
      <div className="p-4 border-t border-slate-700/50 bg-slate-900/50">
        <div className="space-y-2">
          <button className="w-full flex items-center px-4 py-2.5 text-sm font-medium text-gray-300 hover:text-white hover:bg-slate-700/40 rounded-lg transition-all duration-200 relative group">
            <Bell className="w-4 h-4 flex-shrink-0 group-hover:animate-pulse" />
            {(!sidebarCollapsed || isMobile) && (
              <span className="ml-3 truncate">Notifications</span>
            )}
            <div className="absolute top-2 left-6 w-2 h-2 bg-gradient-to-r from-red-400 to-red-500 rounded-full animate-pulse shadow-lg shadow-red-500/50"></div>
          </button>
          <button
            onClick={() => signOut()}
            className="w-full flex items-center px-4 py-2.5 text-sm font-medium text-red-400 hover:text-red-300 hover:bg-red-900/20 border border-transparent hover:border-red-800/30 rounded-lg transition-all duration-200 group"
          >
            <LogOut className="w-4 h-4 flex-shrink-0 group-hover:translate-x-1 transition-transform duration-200" />
            {(!sidebarCollapsed || isMobile) && (
              <span className="ml-3 truncate">Sign Out</span>
            )}
          </button>
        </div>
        
        {(!sidebarCollapsed || isMobile) && (
          <div className="mt-4 pt-4 border-t border-slate-700/30">
            <div className="text-xs text-gray-500 text-center">
              Vantage v2.1.0
            </div>
            <div className="text-xs text-gray-600 text-center mt-1">
              © 2024 Satellite Intelligence
            </div>
          </div>
        )}
      </div>
    </div>
  );

  return (
    <>
      {/* Mobile Menu Button */}
      <div className="lg:hidden fixed top-4 left-4 z-50">
        <button
          onClick={() => setMobileMenuOpen(true)}
          className="p-2 bg-slate-800 text-white rounded-lg shadow-lg border border-slate-700"
        >
          <Menu className="w-5 h-5" />
        </button>
      </div>

      {/* Desktop Sidebar */}
      <div className={`hidden lg:flex lg:flex-col lg:fixed lg:inset-y-0 lg:left-0 lg:z-50 bg-gradient-to-b from-slate-800 to-slate-900 border-r border-slate-700/50 backdrop-blur-xl transition-all duration-150 shadow-2xl ${
        sidebarCollapsed ? 'lg:w-16' : 'lg:w-64'
      }`}>
        <SidebarContent />
      </div>

      {/* Mobile Sidebar */}
      <div className={`lg:hidden fixed inset-0 z-50 ${mobileMenuOpen ? 'block' : 'hidden'}`}>
        <div className="fixed inset-0 bg-black bg-opacity-50" onClick={() => setMobileMenuOpen(false)}></div>
        <div className="fixed inset-y-0 left-0 w-64 bg-gradient-to-b from-slate-800 to-slate-900 border-r border-slate-700/50 shadow-2xl">
          <SidebarContent isMobile={true} />
        </div>
      </div>
    </>
  );
};

export default Navigation;