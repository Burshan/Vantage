import React, { useState } from 'react';
import { Calendar, X } from 'lucide-react';

const CreateAOIModal = ({ 
  isOpen, 
  onClose, 
  onCreate, 
  isProcessing,
  initialData = {
    name: '',
    description: '',
    location: '',
    classification: 'CONFIDENTIAL',
    priority: 'MEDIUM',
    color: '#3B82F6',
    coords: [34.876149, 50.964594, 34.911741, 51.025335]
  }
}) => {
  const [formData, setFormData] = useState(initialData);

  if (!isOpen) return null;

  const handleSubmit = () => {
    if (!formData.name.trim()) {
      alert('Please enter an AOI name');
      return;
    }

    if (!formData.coords || formData.coords.length !== 4) {
      alert('Please enter valid bounding box coordinates');
      return;
    }

    onCreate(formData);
  };

  const handleCoordinateChange = (index, value) => {
    const newCoords = [...formData.coords];
    newCoords[index] = parseFloat(value) || 0;
    setFormData({ ...formData, coords: newCoords });
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-slate-800 border border-slate-700 rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-slate-700 flex justify-between items-center">
          <div>
            <h2 className="text-xl font-bold text-white">Create New Area of Interest</h2>
            <p className="text-gray-400 text-sm mt-1">Define a geographic area for automated satellite monitoring</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        
        <div className="p-6 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">AOI Name *</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full p-3 bg-slate-700 border border-slate-600 rounded text-white placeholder-gray-400"
                placeholder="e.g., Tehran Industrial Complex"
                disabled={isProcessing}
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Location Name</label>
              <input
                type="text"
                value={formData.location}
                onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                className="w-full p-3 bg-slate-700 border border-slate-600 rounded text-white placeholder-gray-400"
                placeholder="Geographic identifier"
                disabled={isProcessing}
              />
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Description</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full p-3 bg-slate-700 border border-slate-600 rounded text-white placeholder-gray-400 h-24"
              placeholder="Describe the strategic importance and monitoring objectives..."
              disabled={isProcessing}
            />
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Classification</label>
              <select
                value={formData.classification}
                onChange={(e) => setFormData({ ...formData, classification: e.target.value })}
                className="w-full p-3 bg-slate-700 border border-slate-600 rounded text-white"
                disabled={isProcessing}
              >
                <option value="UNCLASSIFIED">Unclassified</option>
                <option value="CONFIDENTIAL">Confidential</option>
                <option value="SECRET">Secret</option>
                <option value="TOP_SECRET">Top Secret</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Priority</label>
              <select
                value={formData.priority}
                onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                className="w-full p-3 bg-slate-700 border border-slate-600 rounded text-white"
                disabled={isProcessing}
              >
                <option value="LOW">Low</option>
                <option value="MEDIUM">Medium</option>
                <option value="HIGH">High</option>
                <option value="CRITICAL">Critical</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Color Code</label>
              <input
                type="color"
                value={formData.color}
                onChange={(e) => setFormData({ ...formData, color: e.target.value })}
                className="w-full h-12 bg-slate-700 border border-slate-600 rounded cursor-pointer"
                disabled={isProcessing}
              />
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Bounding Box Coordinates</label>
            <p className="text-xs text-gray-400 mb-3">Define rectangular area bounds in decimal degrees</p>
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-slate-700/50 rounded-lg p-3">
                <div className="flex items-center mb-2">
                  <span className="w-2 h-2 bg-red-400 rounded-full mr-2"></span>
                  <label className="block text-xs font-medium text-gray-300">Southwest Corner</label>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <input
                      type="number"
                      step="0.000001"
                      value={formData.coords[0]}
                      onChange={(e) => handleCoordinateChange(0, e.target.value)}
                      className="w-full p-2 bg-slate-700 border border-slate-600 rounded text-white text-sm"
                      placeholder="Min Latitude"
                      disabled={isProcessing}
                    />
                    <label className="block text-xs text-gray-500 mt-1">Latitude (South)</label>
                  </div>
                  <div>
                    <input
                      type="number"
                      step="0.000001"
                      value={formData.coords[1]}
                      onChange={(e) => handleCoordinateChange(1, e.target.value)}
                      className="w-full p-2 bg-slate-700 border border-slate-600 rounded text-white text-sm"
                      placeholder="Min Longitude"
                      disabled={isProcessing}
                    />
                    <label className="block text-xs text-gray-500 mt-1">Longitude (West)</label>
                  </div>
                </div>
              </div>
              
              <div className="bg-slate-700/50 rounded-lg p-3">
                <div className="flex items-center mb-2">
                  <span className="w-2 h-2 bg-green-400 rounded-full mr-2"></span>
                  <label className="block text-xs font-medium text-gray-300">Northeast Corner</label>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <input
                      type="number"
                      step="0.000001"
                      value={formData.coords[2]}
                      onChange={(e) => handleCoordinateChange(2, e.target.value)}
                      className="w-full p-2 bg-slate-700 border border-slate-600 rounded text-white text-sm"
                      placeholder="Max Latitude"
                      disabled={isProcessing}
                    />
                    <label className="block text-xs text-gray-500 mt-1">Latitude (North)</label>
                  </div>
                  <div>
                    <input
                      type="number"
                      step="0.000001"
                      value={formData.coords[3]}
                      onChange={(e) => handleCoordinateChange(3, e.target.value)}
                      className="w-full p-2 bg-slate-700 border border-slate-600 rounded text-white text-sm"
                      placeholder="Max Longitude"
                      disabled={isProcessing}
                    />
                    <label className="block text-xs text-gray-500 mt-1">Longitude (East)</label>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <div className="bg-blue-900/20 border border-blue-700 rounded-lg p-4">
            <div className="flex items-start">
              <Calendar className="w-5 h-5 text-blue-400 mr-3 mt-0.5" />
              <div>
                <h4 className="text-blue-300 font-medium">Automated Monitoring</h4>
                <p className="text-blue-200 text-sm mt-1">
                  This AOI will be automatically analyzed every week. Each analysis consumes 1 token from your account balance.
                </p>
              </div>
            </div>
          </div>
        </div>
        
        <div className="p-6 border-t border-slate-700 flex justify-end space-x-3">
          <button
            onClick={onClose}
            disabled={isProcessing}
            className="px-4 py-2 bg-slate-600 hover:bg-slate-700 disabled:bg-gray-600 text-white rounded transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={!formData.name.trim() || isProcessing}
            className="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded font-medium transition-colors flex items-center"
          >
            {isProcessing && <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>}
            {isProcessing ? 'Creating...' : 'Create AOI'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default CreateAOIModal;