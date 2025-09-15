import React, { useState, useEffect } from 'react';
import { 
  Wifi, WifiOff, Server, Database, Globe, Shield, 
  AlertCircle, CheckCircle, Clock, Zap 
} from 'lucide-react';

const SystemStatus = ({ className }) => {
  const [systemHealth, setSystemHealth] = useState({
    api: { status: 'healthy', latency: 45, uptime: 99.9 },
    satellite: { status: 'healthy', lastUpdate: new Date(), activeConnections: 8 },
    database: { status: 'healthy', queries: 1247, performance: 98.5 },
    processing: { status: 'healthy', queue: 3, throughput: 156 }
  });

  useEffect(() => {
    const interval = setInterval(() => {
      setSystemHealth(prev => ({
        ...prev,
        api: {
          ...prev.api,
          latency: Math.max(20, Math.min(200, prev.api.latency + (Math.random() - 0.5) * 10))
        },
        satellite: {
          ...prev.satellite,
          activeConnections: Math.max(1, Math.min(12, prev.satellite.activeConnections + Math.round((Math.random() - 0.5) * 2)))
        },
        database: {
          ...prev.database,
          queries: prev.database.queries + Math.round(Math.random() * 10),
          performance: Math.max(85, Math.min(100, prev.database.performance + (Math.random() - 0.5) * 2))
        },
        processing: {
          ...prev.processing,
          queue: Math.max(0, Math.min(10, prev.processing.queue + Math.round((Math.random() - 0.5) * 2))),
          throughput: Math.max(100, Math.min(300, prev.processing.throughput + (Math.random() - 0.5) * 20))
        }
      }));
    }, 3000);

    return () => clearInterval(interval);
  }, [systemHealth]);

  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy': return 'emerald';
      case 'warning': return 'amber';
      case 'error': return 'red';
      default: return 'slate';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'healthy': return CheckCircle;
      case 'warning': return AlertCircle;
      case 'error': return AlertCircle;
      default: return Clock;
    }
  };

  const ServiceCard = ({ icon: Icon, title, status, metrics }) => {
    const colorClass = getStatusColor(status);
    const StatusIcon = getStatusIcon(status);
    
    const colorStyles = {
      emerald: {
        bg: 'bg-emerald-500/20',
        text: 'text-emerald-400',
        pulse: 'bg-emerald-400'
      },
      amber: {
        bg: 'bg-amber-500/20',
        text: 'text-amber-400',
        pulse: 'bg-amber-400'
      },
      red: {
        bg: 'bg-red-500/20',
        text: 'text-red-400',
        pulse: 'bg-red-400'
      },
      slate: {
        bg: 'bg-slate-500/20',
        text: 'text-slate-400',
        pulse: 'bg-slate-400'
      }
    };

    const colors = colorStyles[colorClass] || colorStyles.emerald;
    
    return (
      <div className="bg-gradient-to-br from-slate-800/60 to-slate-900/60 backdrop-blur border border-slate-700/40 rounded-xl p-4 hover:border-slate-600/50 transition-all duration-300 group">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-3">
            <div className={`p-2 ${colors.bg} rounded-lg`}>
              <Icon className={`w-4 h-4 ${colors.text}`} />
            </div>
            <div>
              <h4 className="text-sm font-medium text-white">{title}</h4>
              <div className="flex items-center space-x-2 mt-0.5">
                <StatusIcon className={`w-3 h-3 ${colors.text}`} />
                <span className={`text-xs font-medium ${colors.text} capitalize`}>
                  {status}
                </span>
              </div>
            </div>
          </div>
          <div className={`w-2 h-2 ${colors.pulse} rounded-full animate-pulse`} />
        </div>
        
        <div className="space-y-2">
          {metrics.map((metric, index) => (
            <div key={index} className="flex justify-between items-center text-xs">
              <span className="text-slate-400">{metric.label}</span>
              <span className="text-white font-medium">{metric.value}</span>
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className={`space-y-4 ${className}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-blue-500/20 rounded-xl">
            <Server className="w-5 h-5 text-blue-400" />
          </div>
          <div>
            <h3 className="text-lg font-medium text-white tracking-tight">System Status</h3>
            <p className="text-sm text-slate-400">Real-time infrastructure monitoring</p>
          </div>
        </div>
        
        <div className="flex items-center space-x-2 text-xs text-emerald-400">
          <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
          <span className="font-medium">All Systems Operational</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <ServiceCard
          icon={Globe}
          title="API Gateway"
          status={systemHealth.api.status}
          metrics={[
            { label: 'Latency', value: `${Math.round(systemHealth.api.latency)}ms` },
            { label: 'Uptime', value: `${systemHealth.api.uptime.toFixed(1)}%` }
          ]}
        />

        <ServiceCard
          icon={Wifi}
          title="Satellite Link"
          status={systemHealth.satellite.status}
          metrics={[
            { label: 'Connections', value: systemHealth.satellite.activeConnections },
            { label: 'Last Update', value: 'Now' }
          ]}
        />

        <ServiceCard
          icon={Database}
          title="Database"
          status={systemHealth.database.status}
          metrics={[
            { label: 'Queries/min', value: Math.round(systemHealth.database.queries) },
            { label: 'Performance', value: `${systemHealth.database.performance.toFixed(1)}%` }
          ]}
        />

        <ServiceCard
          icon={Zap}
          title="Processing"
          status={systemHealth.processing.status}
          metrics={[
            { label: 'Queue', value: `${systemHealth.processing.queue} jobs` },
            { label: 'Throughput', value: `${Math.round(systemHealth.processing.throughput)}/hr` }
          ]}
        />
      </div>
    </div>
  );
};

export default SystemStatus;