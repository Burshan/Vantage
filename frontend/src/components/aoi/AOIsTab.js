import React from 'react';
import { Plus, MapPin } from 'lucide-react';
import AOICard from './AOICard';

const AOIsTab = ({ 
  aois, 
  analysisHistory, 
  userProfile,
  onCreateAOI, 
  onViewDashboard, 
  onDeleteAOI,
  isProcessing
}) => {
  return (
    <div className="space-y-6">
      {/* Premium Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-light text-white tracking-tight">Areas of Interest</h2>
          <p className="text-slate-400 text-sm mt-2 font-medium">Manage your satellite monitoring locations</p>
        </div>
        <div className="relative">
          <button
            onClick={onCreateAOI}
            disabled={isProcessing || !userProfile || userProfile.tokens_remaining <= 0}
            className="bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 disabled:from-gray-600 disabled:to-gray-700 text-white px-6 py-3 rounded-xl font-medium flex items-center transition-all duration-300 shadow-lg shadow-blue-500/25 hover:shadow-xl hover:shadow-blue-500/30 hover:scale-[1.02] disabled:hover:scale-100"
            title={!userProfile || userProfile.tokens_remaining <= 0 ? "Need 1 token to create AOI" : "Create new Area of Interest"}
          >
            <Plus className="w-5 h-5 mr-2" />
            Create AOI
          </button>
          {(!userProfile || userProfile.tokens_remaining <= 0) && (
            <div className="absolute -top-2 -right-2 bg-red-500 text-white text-xs px-2 py-1 rounded-full">
              No tokens
            </div>
          )}
        </div>
      </div>
      
      {aois.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
          {aois.map(aoi => (
            <AOICard 
              key={aoi.id} 
              aoi={aoi}
              analysisHistory={analysisHistory}
              onViewDashboard={onViewDashboard}
              onDelete={onDeleteAOI}
              isProcessing={isProcessing}
            />
          ))}
        </div>
      ) : (
        <div className="bg-gradient-to-br from-slate-800/60 to-slate-900/60 backdrop-blur border border-slate-700/40 rounded-2xl p-12 text-center shadow-2xl">
          <div className="p-4 bg-slate-700/30 rounded-2xl inline-block mb-6">
            <MapPin className="w-16 h-16 text-slate-400" />
          </div>
          <h3 className="text-white text-xl font-medium mb-3 tracking-tight">No Areas of Interest</h3>
          <p className="text-slate-400 mb-8 max-w-md mx-auto leading-relaxed">Create your first AOI to begin automated satellite monitoring and change detection</p>
          <button
            onClick={onCreateAOI}
            disabled={isProcessing}
            className="bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 disabled:from-gray-600 disabled:to-gray-700 text-white px-8 py-3 rounded-xl font-medium transition-all duration-300 shadow-lg shadow-blue-500/25 hover:shadow-xl hover:shadow-blue-500/30 hover:scale-[1.02] disabled:hover:scale-100"
          >
            Create First AOI
          </button>
        </div>
      )}
    </div>
  );
};

export default AOIsTab;