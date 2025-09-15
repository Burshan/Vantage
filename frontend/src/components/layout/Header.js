import React from 'react';
import { UserButton } from '@clerk/clerk-react';
import { Globe } from 'lucide-react';

const Header = ({ userProfile }) => {
  return (
    <header className="bg-slate-800 border-b border-slate-700">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center mr-3">
              <Globe className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">VANTAGE</h1>
              <p className="text-xs text-gray-400">Satellite Intelligence Platform</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            <div className="text-right">
              <div className="text-white font-medium text-sm">
                {userProfile?.first_name} {userProfile?.last_name}
              </div>
              <div className="text-xs text-gray-400">
                {userProfile?.tokens_remaining || 0} tokens remaining
              </div>
            </div>
            <UserButton afterSignOutUrl="/" />
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;