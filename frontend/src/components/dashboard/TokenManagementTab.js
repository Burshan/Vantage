import React from 'react';
import { AlertTriangle, Zap, TrendingUp, Calendar, CreditCard, Plus } from 'lucide-react';

const TokenManagementTab = ({ userProfile, aoisCount }) => {
  const tokensRemaining = userProfile?.tokens_remaining || 0;
  const tokensUsed = userProfile?.total_tokens_used || 0;
  const isLowBalance = tokensRemaining <= 10;

  // Calculate estimated weekly consumption (placeholder calculation)
  const estimatedWeeklyConsumption = aoisCount * 7; // Rough estimate: 1 token per AOI per day

  return (
    <div className="space-y-6">
      {/* Premium Header */}
      <div>
        <h2 className="text-3xl font-light text-white tracking-tight">Token Management</h2>
        <p className="text-slate-400 text-sm mt-2 font-medium">Monitor and manage your satellite analysis credits</p>
      </div>
      
      {/* Premium Balance Card */}
      <div className="bg-gradient-to-br from-blue-500/20 to-purple-500/20 backdrop-blur border border-blue-500/30 rounded-2xl p-8 shadow-2xl">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-2xl font-medium text-white tracking-tight">Current Balance</h3>
            <p className="text-blue-200 mt-1 font-medium">Available for satellite monitoring operations</p>
          </div>
          <div className="text-right">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-emerald-400 rounded-full animate-pulse"></div>
              <div className="text-5xl font-light text-white">{tokensRemaining}</div>
            </div>
            <div className="text-sm text-blue-200 mt-2">
              {tokensUsed} credits consumed total
            </div>
          </div>
        </div>
        
        {isLowBalance && (
          <div className="mt-6 p-4 bg-amber-500/20 backdrop-blur border border-amber-500/40 rounded-xl">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-amber-500/20 rounded-xl">
                <AlertTriangle className="w-5 h-5 text-amber-400" />
              </div>
              <div>
                <div className="text-amber-300 font-medium">Low Balance Alert</div>
                <div className="text-amber-200 text-sm mt-0.5">
                  Consider purchasing more credits to maintain continuous monitoring
                </div>
              </div>
              <button className="ml-auto bg-amber-500 hover:bg-amber-600 text-white px-4 py-2 rounded-xl text-sm font-medium transition-all duration-300 hover:scale-105">
                <Plus className="w-4 h-4 inline mr-1" />
                Add Credits
              </button>
            </div>
          </div>
        )}
      </div>
      
      {/* Premium Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-gradient-to-br from-slate-800/80 to-slate-900/80 backdrop-blur border border-slate-700/50 rounded-2xl p-6 text-center hover:border-slate-600/50 transition-all duration-300 shadow-xl">
          <div className="p-3 bg-emerald-500/20 rounded-2xl inline-block mb-4">
            <Zap className="w-8 h-8 text-emerald-400" />
          </div>
          <div className="text-3xl font-light text-white mb-2">
            {tokensRemaining}
          </div>
          <div className="text-slate-400 text-sm font-medium tracking-wide">Available Credits</div>
        </div>
        
        <div className="bg-gradient-to-br from-slate-800/80 to-slate-900/80 backdrop-blur border border-slate-700/50 rounded-2xl p-6 text-center hover:border-slate-600/50 transition-all duration-300 shadow-xl">
          <div className="p-3 bg-purple-500/20 rounded-2xl inline-block mb-4">
            <TrendingUp className="w-8 h-8 text-purple-400" />
          </div>
          <div className="text-3xl font-light text-white mb-2">
            {tokensUsed}
          </div>
          <div className="text-slate-400 text-sm font-medium tracking-wide">Total Consumed</div>
        </div>
        
        <div className="bg-gradient-to-br from-slate-800/80 to-slate-900/80 backdrop-blur border border-slate-700/50 rounded-2xl p-6 text-center hover:border-slate-600/50 transition-all duration-300 shadow-xl">
          <div className="p-3 bg-blue-500/20 rounded-2xl inline-block mb-4">
            <Calendar className="w-8 h-8 text-blue-400" />
          </div>
          <div className="text-3xl font-light text-white mb-2">
            ~{estimatedWeeklyConsumption}
          </div>
          <div className="text-slate-400 text-sm font-medium tracking-wide">Est. Weekly Usage</div>
        </div>
      </div>

      {/* Premium Purchase Options */}
      <div className="bg-gradient-to-br from-slate-800/60 to-slate-900/60 backdrop-blur border border-slate-700/40 rounded-2xl p-6 shadow-2xl">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-xl font-medium text-white tracking-tight">Purchase Credits</h3>
            <p className="text-slate-400 text-sm mt-1">Select a credit package to continue monitoring operations</p>
          </div>
          <div className="p-2 bg-blue-500/20 rounded-xl">
            <CreditCard className="w-6 h-6 text-blue-400" />
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-slate-700/40 backdrop-blur border border-slate-600/40 rounded-xl p-4 hover:border-slate-500/60 transition-all duration-300 hover:scale-[1.02]">
            <div className="text-center">
              <div className="text-2xl font-light text-white mb-1">100</div>
              <div className="text-slate-400 text-sm mb-3">Credits</div>
              <div className="text-xl font-medium text-blue-400 mb-4">$29</div>
              <button className="w-full bg-slate-600/60 hover:bg-slate-500/80 text-white py-2 px-4 rounded-lg text-sm font-medium transition-all duration-300">
                Purchase
              </button>
            </div>
          </div>
          
          <div className="bg-gradient-to-br from-blue-500/20 to-purple-500/20 backdrop-blur border border-blue-500/40 rounded-xl p-4 relative">
            <div className="absolute -top-2 left-1/2 transform -translate-x-1/2">
              <span className="bg-blue-500 text-white px-3 py-1 rounded-full text-xs font-medium">Popular</span>
            </div>
            <div className="text-center mt-2">
              <div className="text-2xl font-light text-white mb-1">500</div>
              <div className="text-slate-400 text-sm mb-3">Credits</div>
              <div className="text-xl font-medium text-blue-400 mb-4">$129</div>
              <button className="w-full bg-blue-500 hover:bg-blue-600 text-white py-2 px-4 rounded-lg text-sm font-medium transition-all duration-300 hover:scale-105">
                Purchase
              </button>
            </div>
          </div>
          
          <div className="bg-slate-700/40 backdrop-blur border border-slate-600/40 rounded-xl p-4 hover:border-slate-500/60 transition-all duration-300 hover:scale-[1.02]">
            <div className="text-center">
              <div className="text-2xl font-light text-white mb-1">1000</div>
              <div className="text-slate-400 text-sm mb-3">Credits</div>
              <div className="text-xl font-medium text-blue-400 mb-4">$199</div>
              <button className="w-full bg-slate-600/60 hover:bg-slate-500/80 text-white py-2 px-4 rounded-lg text-sm font-medium transition-all duration-300">
                Purchase
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TokenManagementTab;