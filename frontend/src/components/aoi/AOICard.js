import React from 'react';
import { Eye, Trash2 } from 'lucide-react';

const AOICard = ({ 
  aoi, 
  analysisHistory, 
  onViewDashboard, 
  onDelete, 
  isProcessing
}) => {
  const lastAnalysis = analysisHistory.find(h => h.aoi?.name === aoi.name);
  const isDeleting = aoi.status === 'deleting';
  const isCreating = aoi.status === 'creating';
  const isCreated = aoi.status === 'created';
  
  return (
    <div className={`bg-gradient-to-br from-slate-800/60 to-slate-900/60 backdrop-blur border rounded-2xl p-6 transition-all duration-300 shadow-xl hover:shadow-2xl ${
      isDeleting ? 'opacity-50 border-red-500/60 shadow-red-500/10' : 
      isCreating ? 'opacity-75 border-blue-500/60 shadow-blue-500/10' : 
      isCreated ? 'border-emerald-500/60 shadow-emerald-500/10' : 
      'border-slate-700/40 hover:border-slate-600/50 hover:scale-[1.02]'
    }`}>
      <div className="flex items-start justify-between mb-6">
        <div className="flex items-center">
          <div 
            className="w-5 h-5 rounded-full mr-4 border-2 border-white/30 shadow-lg"
            style={{ 
              backgroundColor: aoi.color_code,
              boxShadow: `0 0 20px ${aoi.color_code}40`
            }}
          />
          <div>
            <h3 className="text-white font-medium text-lg tracking-tight">{aoi.name}</h3>
            <p className="text-slate-400 text-sm mt-0.5">{aoi.location_name}</p>
          </div>
        </div>
        
        <div className="flex space-x-2">
          <button
            onClick={() => onViewDashboard(aoi.id)}
            disabled={isProcessing || isDeleting || isCreating || isCreated}
            className="p-2.5 bg-blue-500/80 hover:bg-blue-600/90 disabled:bg-slate-600/50 disabled:cursor-not-allowed text-white rounded-xl transition-all duration-300 hover:scale-110 hover:shadow-lg shadow-blue-500/25"
            title="View AOI Dashboard"
          >
            <Eye className="w-4 h-4" />
          </button>
          <button
            onClick={() => onDelete(aoi.id)}
            disabled={isProcessing || isDeleting || isCreating || isCreated}
            className="p-2.5 bg-red-500/80 hover:bg-red-600/90 disabled:bg-slate-600/50 text-white rounded-xl transition-all duration-300 hover:scale-110 hover:shadow-lg shadow-red-500/25"
            title="Delete AOI"
          >
            {isDeleting ? (
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
            ) : (
              <Trash2 className="w-4 h-4" />
            )}
          </button>
        </div>
      </div>
      
      <p className="text-slate-300 text-sm mb-6 line-clamp-2 leading-relaxed">{aoi.description}</p>
      
      {/* Premium Status indicator */}
      {(isCreating || isCreated || isDeleting) && (
        <div className={`text-xs px-3 py-2 rounded-xl mb-6 font-medium backdrop-blur border ${
          isCreating ? 'bg-blue-500/20 text-blue-300 border-blue-500/30' :
          isCreated ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30' :
          'bg-red-500/20 text-red-300 border-red-500/30'
        }`}>
          {isCreating && 'Creating AOI...'}
          {isCreated && 'Processing baseline...'}
          {isDeleting && 'Deleting...'}
        </div>
      )}
      
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <span className="text-slate-400 text-sm font-medium">Classification:</span>
          <span className={`px-3 py-1.5 text-xs rounded-full font-medium backdrop-blur border ${
            aoi.classification === 'TOP_SECRET' ? 'bg-red-500/20 text-red-300 border-red-500/30' :
            aoi.classification === 'SECRET' ? 'bg-orange-500/20 text-orange-300 border-orange-500/30' :
            aoi.classification === 'CONFIDENTIAL' ? 'bg-amber-500/20 text-amber-300 border-amber-500/30' :
            'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
          }`}>
            {aoi.classification}
          </span>
        </div>
        
        <div className="flex justify-between items-center">
          <span className="text-slate-400 text-sm font-medium">Priority:</span>
          <span className={`px-3 py-1.5 text-xs rounded-full font-medium backdrop-blur border ${
            aoi.priority === 'CRITICAL' ? 'bg-red-500/20 text-red-300 border-red-500/30' :
            aoi.priority === 'HIGH' ? 'bg-orange-500/20 text-orange-300 border-orange-500/30' :
            aoi.priority === 'MEDIUM' ? 'bg-amber-500/20 text-amber-300 border-amber-500/30' :
            'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
          }`}>
            {aoi.priority}
          </span>
        </div>
        
        <div className="border-t border-slate-700/50 pt-4">
          <div className="flex justify-between items-center text-sm mb-3">
            <span className="text-slate-400 font-medium">Last Analysis:</span>
            <span className="text-white font-medium">
              {lastAnalysis ? new Date(lastAnalysis.analysis_timestamp).toLocaleDateString() : 'Never'}
            </span>
          </div>
          <div className="flex justify-between items-center text-sm">
            <span className="text-slate-400 font-medium">Baseline Status:</span>
            <div className="flex items-center space-x-2">
              <div className={`w-2 h-2 rounded-full ${aoi.baseline_status === 'completed' ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400 animate-pulse'}`}></div>
              <span className={`text-sm font-medium ${aoi.baseline_status === 'completed' ? 'text-emerald-400' : 'text-amber-400'}`}>
                {aoi.baseline_status || 'pending'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AOICard;