import React from 'react';

const LoadingSpinner = ({ message = "Loading VANTAGE System...", subtitle = "Initializing satellite intelligence platform" }) => {
  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center">
      <div className="text-center">
        <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
        <p className="text-white text-lg">{message}</p>
        {subtitle && <p className="text-gray-400 text-sm">{subtitle}</p>}
      </div>
    </div>
  );
};

export default LoadingSpinner;