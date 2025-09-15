import React from 'react';
import { BarChart3 } from 'lucide-react';

const HistoryTab = ({ analysisHistory }) => {
  // Helper function to get change level and color
  const getChangeLevel = (percentage) => {
    if (!percentage) return 'unknown';
    if (percentage >= 15) return 'high';
    if (percentage >= 5) return 'medium';
    return 'low';
  };

  const getChangeColor = (level) => {
    switch (level) {
      case 'high': return 'text-red-400';
      case 'medium': return 'text-amber-400';
      case 'low': return 'text-emerald-400';
      default: return 'text-slate-400';
    }
  };

  return (
    <div className="space-y-6">
      {/* Premium Header */}
      <div>
        <h2 className="text-3xl font-light text-white tracking-tight">Analysis History</h2>
        <p className="text-slate-400 text-sm mt-2 font-medium">Complete chronological record of all satellite analyses</p>
      </div>
      
      <div className="bg-gradient-to-br from-slate-800/60 to-slate-900/60 backdrop-blur border border-slate-700/40 rounded-2xl overflow-hidden shadow-2xl">
        {analysisHistory.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-700/50 backdrop-blur border-b border-slate-600/50">
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider">
                    AOI / Analysis
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider">
                    Date & Time
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider">
                    Change
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider">
                    Status
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700/40">
                {analysisHistory.map(analysis => {
                  const changeLevel = getChangeLevel(analysis.change_percentage);
                  return (
                    <tr key={analysis.id} className="hover:bg-slate-700/30 transition-all duration-300">
                      <td className="px-6 py-5 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="w-4 h-4 rounded-full mr-4 bg-blue-500/80 shadow-lg shadow-blue-500/50"></div>
                          <div>
                            <div className="text-white font-medium">
                              {analysis.aoi ? analysis.aoi.name : 'Manual Analysis'}
                            </div>
                            <div className="text-slate-400 text-sm mt-0.5">
                              {analysis.aoi?.location_name || 'Default Region'}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-5 whitespace-nowrap">
                        <div className="text-white text-sm font-medium">
                          {new Date(analysis.analysis_timestamp).toLocaleDateString()}
                        </div>
                        <div className="text-slate-400 text-xs mt-0.5">
                          {new Date(analysis.analysis_timestamp).toLocaleTimeString()}
                        </div>
                      </td>
                      <td className="px-6 py-5 whitespace-nowrap">
                        <span className="px-3 py-1.5 text-xs font-medium rounded-full bg-blue-500/20 text-blue-300 border border-blue-500/30 backdrop-blur">
                          {analysis.operation_name || 'Analysis'}
                        </span>
                      </td>
                      <td className="px-6 py-5 whitespace-nowrap">
                        <div className="flex items-center space-x-2">
                          <div className={`w-2 h-2 rounded-full ${
                            changeLevel === 'high' ? 'bg-red-400 animate-pulse' : 
                            changeLevel === 'medium' ? 'bg-amber-400 animate-pulse' : 
                            changeLevel === 'low' ? 'bg-emerald-400 animate-pulse' : 
                            'bg-slate-400'
                          }`}></div>
                          <span className={`text-sm font-medium ${getChangeColor(changeLevel)}`}>
                            {analysis.change_percentage ? `${analysis.change_percentage.toFixed(2)}%` : 'N/A'}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-5 whitespace-nowrap">
                        <span className="px-3 py-1.5 text-xs font-medium rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 backdrop-blur">
                          {analysis.status || 'completed'}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-16">
            <div className="p-4 bg-slate-700/30 rounded-2xl inline-block mb-6">
              <BarChart3 className="w-16 h-16 text-slate-400" />
            </div>
            <h3 className="text-white text-xl font-medium mb-3 tracking-tight">No Analysis History</h3>
            <p className="text-slate-400 leading-relaxed">Your analysis history will appear here once you run your first satellite analysis</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default HistoryTab;