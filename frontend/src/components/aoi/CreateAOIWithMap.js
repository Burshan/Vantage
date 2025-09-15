import React, { useState, useEffect } from 'react';
import { 
  X, MapPin, Globe, Layers, AlertTriangle, CheckCircle, 
  Square, Pentagon, Info, Satellite, Calendar, Shield
} from 'lucide-react';
import AOIMapDrawer from '../map/AOIMapDrawer';

const CreateAOIWithMap = ({ isOpen, onClose, onSubmit, existingAOI = null }) => {
  const [formData, setFormData] = useState({
    name: '',
    location_name: '',
    bbox_coordinates: [],
    priority: 'MEDIUM',
    classification: 'UNCLASSIFIED',
    monitoring_frequency: 'WEEKLY',
    description: ''
  });

  const [aoiInfo, setAOIInfo] = useState({
    area: 0,
    type: null,
    isValid: false
  });

  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Load existing AOI data if editing
  useEffect(() => {
    if (existingAOI) {
      setFormData({
        name: existingAOI.name || '',
        location_name: existingAOI.location_name || '',
        bbox_coordinates: existingAOI.bbox_coordinates || [],
        priority: existingAOI.priority || 'MEDIUM',
        classification: existingAOI.classification || 'UNCLASSIFIED',
        monitoring_frequency: existingAOI.monitoring_frequency || 'WEEKLY',
        description: existingAOI.description || ''
      });
    }
  }, [existingAOI]);

  // Handle map AOI changes
  const handleAOIChange = (aoiData) => {
    if (aoiData.bbox) {
      setFormData(prev => ({
        ...prev,
        bbox_coordinates: aoiData.bbox
      }));
      
      setAOIInfo({
        area: aoiData.area,
        type: aoiData.type,
        isValid: true
      });
      
      // Clear coordinate errors
      setErrors(prev => ({ ...prev, bbox_coordinates: null }));
    } else {
      setFormData(prev => ({
        ...prev,
        bbox_coordinates: []
      }));
      
      setAOIInfo({
        area: 0,
        type: null,
        isValid: false
      });
    }
  };

  // Handle input changes
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    // Clear field errors on change
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: null }));
    }
  };

  // Validate form
  const validateForm = () => {
    const newErrors = {};

    if (!formData.name.trim()) {
      newErrors.name = 'AOI name is required';
    }

    if (!formData.bbox_coordinates || formData.bbox_coordinates.length !== 4) {
      newErrors.bbox_coordinates = 'Please draw an AOI on the map';
    }

    // Validate bbox coordinates range (expects [lat_min, lon_min, lat_max, lon_max])
    if (formData.bbox_coordinates.length === 4) {
      const [minLat, minLng, maxLat, maxLng] = formData.bbox_coordinates;
      
      if (minLng < -180 || maxLng > 180 || minLat < -90 || maxLat > 90) {
        newErrors.bbox_coordinates = 'Coordinates are out of valid range';
      }
      
      if (minLng >= maxLng || minLat >= maxLat) {
        newErrors.bbox_coordinates = 'Invalid coordinate bounds';
      }

      // Check area limitations (optional)
      if (aoiInfo.area > 10000) { // 10,000 km²
        newErrors.bbox_coordinates = 'AOI area too large (max 10,000 km²)';
      }
      
      if (aoiInfo.area < 1) { // 1 km²
        newErrors.bbox_coordinates = 'AOI area too small (min 1 km²)';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);
    
    try {
      await onSubmit(formData);
      onClose();
    } catch (error) {
      console.error('Error creating/updating AOI:', error);
      setErrors({ submit: 'Failed to save AOI. Please try again.' });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Format coordinates for display (expects [lat_min, lon_min, lat_max, lon_max])
  const formatCoordinates = (bbox) => {
    if (!bbox || bbox.length !== 4) return 'No coordinates selected';
    const [minLat, minLng, maxLat, maxLng] = bbox;
    return `SW: ${minLat.toFixed(4)}, ${minLng.toFixed(4)} | NE: ${maxLat.toFixed(4)}, ${maxLng.toFixed(4)}`;
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-slate-800 rounded-lg shadow-xl w-full max-w-6xl max-h-[95vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-700">
          <div className="flex items-center space-x-3">
            <Satellite className="w-6 h-6 text-blue-400" />
            <h2 className="text-xl font-bold text-white">
              {existingAOI ? 'Edit Area of Interest' : 'Create New Area of Interest'}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        <div className="flex max-h-[calc(95vh-80px)]">
          {/* Left Panel - Form */}
          <div className="w-1/2 p-6 overflow-y-auto">
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Basic Info */}
              <div>
                <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
                  <Info className="w-5 h-5 mr-2 text-blue-400" />
                  Basic Information
                </h3>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      AOI Name *
                    </label>
                    <input
                      type="text"
                      name="name"
                      value={formData.name}
                      onChange={handleInputChange}
                      className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white placeholder-gray-400 focus:border-blue-500 focus:outline-none"
                      placeholder="e.g., Downtown Construction Site"
                    />
                    {errors.name && (
                      <p className="text-red-400 text-sm mt-1">{errors.name}</p>
                    )}
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Location Description
                    </label>
                    <input
                      type="text"
                      name="location_name"
                      value={formData.location_name}
                      onChange={handleInputChange}
                      className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white placeholder-gray-400 focus:border-blue-500 focus:outline-none"
                      placeholder="e.g., New York City, Manhattan"
                    />
                    {errors.location_name && (
                      <p className="text-red-400 text-sm mt-1">{errors.location_name}</p>
                    )}
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Description <span className="text-gray-500 text-xs">(optional)</span>
                    </label>
                    <textarea
                      name="description"
                      value={formData.description}
                      onChange={handleInputChange}
                      rows={3}
                      className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white placeholder-gray-400 focus:border-blue-500 focus:outline-none resize-none"
                      placeholder="Optional description or notes about this AOI..."
                    />
                  </div>
                </div>
              </div>

              {/* Settings */}
              <div>
                <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
                  <Layers className="w-5 h-5 mr-2 text-green-400" />
                  Monitoring Settings
                </h3>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Priority Level
                    </label>
                    <select
                      name="priority"
                      value={formData.priority}
                      onChange={handleInputChange}
                      className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white focus:border-blue-500 focus:outline-none"
                    >
                      <option value="LOW">Low</option>
                      <option value="MEDIUM">Medium</option>
                      <option value="HIGH">High</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      <Shield className="w-4 h-4 inline mr-1" />
                      Classification
                    </label>
                    <select
                      name="classification"
                      value={formData.classification}
                      onChange={handleInputChange}
                      className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white focus:border-blue-500 focus:outline-none"
                    >
                      <option value="UNCLASSIFIED">Unclassified</option>
                      <option value="RESTRICTED">Restricted</option>
                      <option value="CONFIDENTIAL">Confidential</option>
                    </select>
                  </div>

                  <div className="col-span-2">
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      <Calendar className="w-4 h-4 inline mr-1" />
                      Monitoring Frequency
                    </label>
                    <select
                      name="monitoring_frequency"
                      value={formData.monitoring_frequency}
                      onChange={handleInputChange}
                      className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white focus:border-blue-500 focus:outline-none"
                    >
                      <option value="DAILY">Daily</option>
                      <option value="WEEKLY">Weekly</option>
                      <option value="MONTHLY">Monthly</option>
                    </select>
                  </div>
                </div>
              </div>

              {/* Coordinates Info */}
              <div>
                <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
                  <MapPin className="w-5 h-5 mr-2 text-yellow-400" />
                  Coordinates & Area
                </h3>
                
                <div className="bg-slate-700 rounded p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-300">Status:</span>
                    <div className="flex items-center space-x-2">
                      {aoiInfo.isValid ? (
                        <>
                          <CheckCircle className="w-4 h-4 text-green-400" />
                          <span className="text-sm text-green-400">Valid AOI</span>
                        </>
                      ) : (
                        <>
                          <AlertTriangle className="w-4 h-4 text-yellow-400" />
                          <span className="text-sm text-yellow-400">Draw AOI on map</span>
                        </>
                      )}
                    </div>
                  </div>
                  
                  {aoiInfo.isValid && (
                    <>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-300">Area:</span>
                        <span className="text-sm text-white font-mono">
                          {aoiInfo.area.toFixed(2)} km²
                        </span>
                      </div>
                      
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-300">Shape:</span>
                        <div className="flex items-center space-x-1">
                          {aoiInfo.type === 'rectangle' ? (
                            <Square className="w-4 h-4 text-blue-400" />
                          ) : (
                            <Pentagon className="w-4 h-4 text-blue-400" />
                          )}
                          <span className="text-sm text-white capitalize">{aoiInfo.type}</span>
                        </div>
                      </div>
                      
                      <div>
                        <span className="text-sm text-gray-300">Bounds (Lat, Lng):</span>
                        <div className="text-xs text-gray-400 font-mono mt-1 leading-relaxed">
                          {formatCoordinates(formData.bbox_coordinates)}
                        </div>
                      </div>
                    </>
                  )}
                  
                  {errors.bbox_coordinates && (
                    <p className="text-red-400 text-sm">{errors.bbox_coordinates}</p>
                  )}
                </div>
              </div>

              {/* Submit Buttons */}
              <div className="flex justify-end space-x-3 pt-4">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-4 py-2 text-gray-300 hover:text-white transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting || !aoiInfo.isValid}
                  className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white px-6 py-2 rounded flex items-center space-x-2 transition-colors"
                >
                  {isSubmitting ? (
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  ) : (
                    <CheckCircle className="w-4 h-4" />
                  )}
                  <span>{existingAOI ? 'Update AOI' : 'Create AOI'}</span>
                </button>
              </div>

              {errors.submit && (
                <p className="text-red-400 text-sm text-center">{errors.submit}</p>
              )}
            </form>
          </div>

          {/* Right Panel - Map */}
          <div className="w-1/2 flex flex-col border-l border-slate-700/30">
            {/* Minimal Header */}
            <div className="p-6 pb-3">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium text-white tracking-tight">
                  Area Selection
                </h3>
                <div className="flex items-center space-x-2">
                  <div className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-pulse"></div>
                  <span className="text-xs text-emerald-400 font-medium uppercase tracking-wide">Live</span>
                </div>
              </div>
            </div>
            
            {/* Clean Map Container */}
            <div className="flex-1 px-6 pb-6">
              <div className="h-full rounded-lg overflow-hidden shadow-2xl border border-slate-600/20">
                <AOIMapDrawer
                  onAOIChange={handleAOIChange}
                  initialBounds={formData.bbox_coordinates}
                  className="h-full w-full"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CreateAOIWithMap;