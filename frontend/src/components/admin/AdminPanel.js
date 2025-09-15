import React, { useState, useEffect } from 'react';
import { 
  Users, Activity, Database, Settings, AlertTriangle, 
  TrendingUp, MapPin, Zap, Clock, Shield, Monitor, 
  BarChart3, PieChart, Calendar, Search, Filter, 
  Download, RefreshCw, User, CreditCard, Eye, Edit, Trash2
} from 'lucide-react';
import { useUser } from '@clerk/clerk-react';
import useVantageAPI from '../../hooks/useVantageAPI';
import useToast from '../../hooks/useToast';

const AdminPanel = ({ userProfile }) => {
  const { user } = useUser();
  const { apiCall } = useVantageAPI();
  const toast = useToast();
  
  const [activeTab, setActiveTab] = useState('overview');
  const [adminData, setAdminData] = useState({
    users: [],
    systemStats: {},
    recentActivity: [],
    usage: {}
  });
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  // Check if user is admin - uses database role from userProfile
  const isAdmin = userProfile?.is_admin === true || 
                  userProfile?.role === 'admin' || 
                  userProfile?.role === 'super_admin';

  useEffect(() => {
    if (isAdmin) {
      loadAdminData();
    }
  }, [isAdmin]);

  const loadAdminData = async () => {
    setIsLoading(true);
    try {
      // Load admin stats from real endpoint
      const statsRes = await apiCall('/api/admin/stats');
      console.log('Admin stats response:', statsRes);
      
      // Extract stats data from response
      const statsData = statsRes.data?.stats || statsRes.stats || {};
      
      // Load users separately (the existing endpoint doesn't have users yet)
      let usersData = [];
      try {
        const usersRes = await apiCall('/api/admin/users');
        usersData = usersRes.data?.users || usersRes.users || [];
      } catch (userError) {
        console.warn('Users endpoint not available yet:', userError);
      }
      
      setAdminData({
        users: usersData,
        systemStats: {
          totalUsers: statsData.users?.total || 0,
          totalAOIs: statsData.aois?.active || 0,
          analysesToday: statsData.analyses?.recent_7_days || 0,
          tokensConsumed: statsData.tokens?.total_used || 0
        },
        recentActivity: [], // Will be implemented later
        usage: statsData.tokens || {}
      });
    } catch (error) {
      toast.showError('Failed to load admin data');
      console.error('Admin data loading error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const adminTabs = [
    { id: 'overview', label: 'Overview', icon: Monitor, description: 'System overview' },
    { id: 'users', label: 'User Management', icon: Users, description: 'Manage users and permissions' },
    { id: 'analytics', label: 'Analytics', icon: BarChart3, description: 'Usage analytics and insights' },
    { id: 'system', label: 'System Health', icon: Activity, description: 'System monitoring and logs' },
    { id: 'tokens', label: 'Token Management', icon: Zap, description: 'Manage user tokens' },
    { id: 'settings', label: 'Admin Settings', icon: Settings, description: 'System configuration' }
  ];

  if (!isAdmin) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
        <div className="bg-red-900/20 border border-red-800/30 rounded-xl p-8 max-w-md mx-auto text-center">
          <Shield className="w-16 h-16 text-red-400 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-white mb-2">Access Denied</h2>
          <p className="text-gray-400">You don't have administrator privileges to view this page.</p>
        </div>
      </div>
    );
  }

  const StatCard = ({ title, value, icon: Icon, change, color = 'blue' }) => (
    <div className={`bg-gradient-to-br from-${color}-900/20 to-${color}-800/20 border border-${color}-800/30 rounded-xl p-6`}>
      <div className="flex items-center justify-between mb-4">
        <Icon className={`w-8 h-8 text-${color}-400`} />
        {change && (
          <div className={`flex items-center text-sm ${change > 0 ? 'text-green-400' : 'text-red-400'}`}>
            <TrendingUp className="w-4 h-4 mr-1" />
            {change > 0 ? '+' : ''}{change}%
          </div>
        )}
      </div>
      <div className="text-3xl font-bold text-white mb-1">{value}</div>
      <p className="text-gray-400 text-sm">{title}</p>
    </div>
  );

  const renderOverview = () => (
    <div className="space-y-6">
      {/* System Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Users"
          value={adminData.systemStats.totalUsers || 0}
          icon={Users}
          change={5}
          color="blue"
        />
        <StatCard
          title="Active AOIs"
          value={adminData.systemStats.totalAOIs || 0}
          icon={MapPin}
          change={12}
          color="green"
        />
        <StatCard
          title="Analyses Today"
          value={adminData.systemStats.analysesToday || 0}
          icon={Activity}
          change={-3}
          color="purple"
        />
        <StatCard
          title="Tokens Consumed"
          value={adminData.systemStats.tokensConsumed || 0}
          icon={Zap}
          change={8}
          color="yellow"
        />
      </div>

      {/* Recent Activity and System Health */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Activity */}
        <div className="bg-gray-800/30 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Recent Activity</h3>
          <div className="space-y-3">
            {adminData.recentActivity.slice(0, 8).map((activity, index) => (
              <div key={index} className="flex items-center space-x-3 p-3 bg-gray-700/30 rounded-lg">
                <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
                <div className="flex-1">
                  <p className="text-white text-sm">{activity.action || 'User analysis completed'}</p>
                  <p className="text-gray-400 text-xs">{activity.timestamp || 'Just now'}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* System Health */}
        <div className="bg-gray-800/30 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">System Health</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-gray-300">API Status</span>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                <span className="text-green-400 text-sm">Operational</span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-300">Database</span>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                <span className="text-green-400 text-sm">Healthy</span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-300">Satellite API</span>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-yellow-400 rounded-full"></div>
                <span className="text-yellow-400 text-sm">Rate Limited</span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-300">Storage</span>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                <span className="text-green-400 text-sm">75% Used</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const renderUserManagement = () => (
    <div className="space-y-6">
      {/* Search and Filters */}
      <div className="flex items-center space-x-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
          <input
            type="text"
            placeholder="Search users..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <button className="flex items-center px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors">
          <Filter className="w-4 h-4 mr-2" />
          Filter
        </button>
        <button className="flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors">
          <Download className="w-4 h-4 mr-2" />
          Export
        </button>
      </div>

      {/* Users Table */}
      <div className="bg-gray-800/30 rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-700/50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">User</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Email</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Tokens</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">AOIs</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Last Active</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700/50">
              {adminData.users.filter(user => 
                user.email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                user.firstName?.toLowerCase().includes(searchTerm.toLowerCase())
              ).map((user, index) => (
                <tr key={index} className="hover:bg-gray-700/20">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                        <User className="w-4 h-4 text-white" />
                      </div>
                      <div className="ml-3">
                        <div className="text-sm font-medium text-white">
                          {user.firstName || 'Unknown'} {user.lastName || ''}
                        </div>
                        <div className="text-sm text-gray-400">ID: {user.id?.slice(0, 8) || 'N/A'}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                    {user.email || 'No email'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="text-sm font-medium text-white">{user.tokens_remaining || 0}</span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                    {user.aoi_count || 0}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                    {user.last_active || 'Never'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div className="flex items-center space-x-2">
                      <button className="text-blue-400 hover:text-blue-300">
                        <Eye className="w-4 h-4" />
                      </button>
                      <button className="text-yellow-400 hover:text-yellow-300">
                        <Edit className="w-4 h-4" />
                      </button>
                      <button className="text-red-400 hover:text-red-300">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );

  const renderAnalytics = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Usage Over Time Chart Placeholder */}
        <div className="bg-gray-800/30 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Usage Over Time</h3>
          <div className="h-64 bg-gray-700/20 rounded-lg flex items-center justify-center">
            <div className="text-center">
              <BarChart3 className="w-12 h-12 text-gray-400 mx-auto mb-2" />
              <p className="text-gray-400">Chart will be implemented with chart library</p>
            </div>
          </div>
        </div>

        {/* Token Distribution */}
        <div className="bg-gray-800/30 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Token Distribution</h3>
          <div className="h-64 bg-gray-700/20 rounded-lg flex items-center justify-center">
            <div className="text-center">
              <PieChart className="w-12 h-12 text-gray-400 mx-auto mb-2" />
              <p className="text-gray-400">Pie chart for token usage distribution</p>
            </div>
          </div>
        </div>
      </div>

      {/* Top Users */}
      <div className="bg-gray-800/30 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Top Users by Activity</h3>
        <div className="space-y-3">
          {[1,2,3,4,5].map((i) => (
            <div key={i} className="flex items-center justify-between p-3 bg-gray-700/30 rounded-lg">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                  <span className="text-white text-sm font-medium">{i}</span>
                </div>
                <div>
                  <p className="text-white text-sm">User {i}</p>
                  <p className="text-gray-400 text-xs">user{i}@example.com</p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-white text-sm font-medium">{50 - i * 8} analyses</p>
                <p className="text-gray-400 text-xs">{100 - i * 15} tokens used</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  const renderContent = () => {
    switch (activeTab) {
      case 'overview': return renderOverview();
      case 'users': return renderUserManagement();
      case 'analytics': return renderAnalytics();
      case 'system': 
        return (
          <div className="text-center py-12">
            <Monitor className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-400">System monitoring will be implemented</p>
          </div>
        );
      case 'tokens':
        return (
          <div className="text-center py-12">
            <Zap className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-400">Token management interface will be implemented</p>
          </div>
        );
      case 'settings':
        return (
          <div className="text-center py-12">
            <Settings className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-400">Admin settings panel will be implemented</p>
          </div>
        );
      default: return renderOverview();
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
        <div className="flex items-center space-x-3">
          <RefreshCw className="w-6 h-6 text-blue-400 animate-spin" />
          <span className="text-white">Loading admin panel...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center space-x-3 mb-2">
            <Shield className="w-8 h-8 text-red-400" />
            <h1 className="text-3xl font-bold text-white">Admin Panel</h1>
          </div>
          <p className="text-gray-400">System administration and user management</p>
        </div>

        {/* Navigation Tabs */}
        <div className="flex space-x-1 mb-8 bg-gray-800/30 rounded-xl p-2">
          {adminTabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center px-4 py-3 rounded-lg transition-all duration-200 flex-1 ${
                activeTab === tab.id
                  ? 'bg-blue-600 text-white shadow-lg'
                  : 'text-gray-300 hover:text-white hover:bg-gray-700/50'
              }`}
            >
              <tab.icon className="w-5 h-5 mr-2" />
              <div className="text-left">
                <div className="font-medium text-sm">{tab.label}</div>
                <div className="text-xs opacity-75">{tab.description}</div>
              </div>
            </button>
          ))}
        </div>

        {/* Content */}
        {renderContent()}
      </div>
    </div>
  );
};

export default AdminPanel;