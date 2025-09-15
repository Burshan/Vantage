import React from 'react';

const ProcessingOverlay = ({ isVisible, message = "Processing..." }) => {
  if (!isVisible) return null;

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-slate-800 border border-slate-700 p-8 rounded-lg">
        <div className="flex items-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mr-4"></div>
          <span className="text-white text-lg">{message}</span>
        </div>
      </div>
    </div>
  );
};

export default ProcessingOverlay;