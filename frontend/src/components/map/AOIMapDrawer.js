import React, { useState, useEffect } from 'react';
import { MapPin, Trash2 } from 'lucide-react';

const AOIMapDrawer = ({ onAOIChange, initialBounds = null, className = "" }) => {
  const [coordinateString, setCoordinateString] = useState('');
  const [isValid, setIsValid] = useState(false);
  const [coordinateError, setCoordinateError] = useState('');

  // Load initial bounds if provided (expects [lat_min, lon_min, lat_max, lon_max])
  useEffect(() => {
    if (initialBounds && initialBounds.length === 4) {
      const coordStr = initialBounds.join(', ');
      setCoordinateString(coordStr);
      validateCoordinateString(coordStr);
    }
  }, [initialBounds]);

  // Calculate approximate area in km²
  const calculateArea = (bbox) => {
    const [minLng, minLat, maxLng, maxLat] = bbox;
    
    const R = 6371; // Earth's radius in km
    const dLat = (maxLat - minLat) * Math.PI / 180;
    const dLng = (maxLng - minLng) * Math.PI / 180;
    const lat1 = minLat * Math.PI / 180;
    const lat2 = maxLat * Math.PI / 180;
    
    const width = R * Math.cos((lat1 + lat2) / 2) * dLng;
    const height = R * dLat;
    
    return Math.abs(width * height);
  };

  const validateCoordinateString = (coordStr) => {
    setCoordinateError('');
    
    if (!coordStr.trim()) {
      setIsValid(false);
      if (onAOIChange) {
        onAOIChange({ bbox: null, area: 0, type: null, isValid: false });
      }
      return;
    }

    // Parse coordinates from comma-separated string
    const parts = coordStr.split(',').map(part => part.trim());
    
    if (parts.length !== 4) {
      setCoordinateError('Please enter exactly 4 coordinates separated by commas');
      setIsValid(false);
      if (onAOIChange) {
        onAOIChange({ bbox: null, area: 0, type: null, isValid: false });
      }
      return;
    }

    const coords = parts.map(parseFloat);
    
    if (coords.some(isNaN)) {
      setCoordinateError('All coordinates must be valid numbers');
      setIsValid(false);
      if (onAOIChange) {
        onAOIChange({ bbox: null, area: 0, type: null, isValid: false });
      }
      return;
    }

    const [minLat, minLng, maxLat, maxLng] = coords;
    
    // Validate ranges
    if (minLat < -90 || maxLat > 90 || minLat > 90 || maxLat < -90) {
      setCoordinateError('Latitude values must be between -90 and 90');
      setIsValid(false);
      if (onAOIChange) {
        onAOIChange({ bbox: null, area: 0, type: null, isValid: false });
      }
      return;
    }
    
    if (minLng < -180 || maxLng > 180 || minLng > 180 || maxLng < -180) {
      setCoordinateError('Longitude values must be between -180 and 180');
      setIsValid(false);
      if (onAOIChange) {
        onAOIChange({ bbox: null, area: 0, type: null, isValid: false });
      }
      return;
    }
    
    if (minLat >= maxLat || minLng >= maxLng) {
      setCoordinateError('Min values must be less than max values');
      setIsValid(false);
      if (onAOIChange) {
        onAOIChange({ bbox: null, area: 0, type: null, isValid: false });
      }
      return;
    }

    // Valid coordinates
    setIsValid(true);
    const bbox = [minLat, minLng, maxLat, maxLng];
    const area = calculateArea([minLng, minLat, maxLng, maxLat]); // calculateArea still needs lon/lat order
    
    if (onAOIChange) {
      onAOIChange({
        bbox,
        area,
        type: 'rectangle',
        isValid: true
      });
    }
  };

  const handleCoordinateStringChange = (e) => {
    const value = e.target.value;
    setCoordinateString(value);
    validateCoordinateString(value);
  };

  const clearCoordinates = () => {
    setCoordinateString('');
    setIsValid(false);
    setCoordinateError('');
    if (onAOIChange) {
      onAOIChange({
        bbox: null,
        area: 0,
        type: null,
        isValid: false
      });
    }
  };

  const setExampleLocation = (name, bounds) => {
    const [minLng, minLat, maxLng, maxLat] = bounds; // Still lon/lat order for internal examples
    const coordStr = `${minLat}, ${minLng}, ${maxLat}, ${maxLng}`; // Convert to lat, lng format for API
    setCoordinateString(coordStr);
    validateCoordinateString(coordStr);
  };


  return (
    <div className={`relative ${className}`}>
        <div className="bg-slate-700 rounded-lg p-6 h-[400px] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white flex items-center">
            <MapPin className="w-5 h-5 mr-2 text-blue-400" />
            Define AOI Coordinates
          </h3>
          {isValid && (
            <button
              onClick={clearCoordinates}
              className="text-red-400 hover:text-red-300 transition-colors"
              title="Clear coordinates"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* Quick Examples */}
        <div className="mb-4">
          <p className="text-sm text-gray-400 mb-2">Quick Examples:</p>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => setExampleLocation('Los Angeles', [-118.6, 33.9, -118.1, 34.2])}
              className="px-3 py-1 bg-slate-600 hover:bg-slate-500 text-xs text-white rounded transition-colors"
            >
              Los Angeles
            </button>
            <button
              onClick={() => setExampleLocation('NYC', [-74.1, 40.6, -73.9, 40.8])}
              className="px-3 py-1 bg-slate-600 hover:bg-slate-500 text-xs text-white rounded transition-colors"
            >
              NYC
            </button>
            <button
              onClick={() => setExampleLocation('London', [-0.3, 51.4, 0.1, 51.6])}
              className="px-3 py-1 bg-slate-600 hover:bg-slate-500 text-xs text-white rounded transition-colors"
            >
              London
            </button>
          </div>
        </div>

        {/* Simple Coordinate Input */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Enter Coordinates (lat_min, lon_min, lat_max, lon_max)
          </label>
          <input
            type="text"
            value={coordinateString}
            onChange={handleCoordinateStringChange}
            placeholder="33.9, -118.6, 34.2, -118.1"
            className={`w-full px-3 py-2 bg-slate-700 border rounded text-white placeholder-gray-400 focus:outline-none ${
              coordinateError ? 'border-red-500 focus:border-red-500' : 'border-slate-500 focus:border-blue-500'
            }`}
          />
          {coordinateError && (
            <p className="text-red-400 text-sm mt-1">{coordinateError}</p>
          )}
          <p className="text-xs text-gray-400 mt-2">
            Format: latitude_min, longitude_min, latitude_max, longitude_max
          </p>
        </div>

        {/* Minimal Status Display */}
        {isValid && (
          <div className="mt-4 flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-pulse"></div>
              <span className="text-emerald-400 text-sm font-medium">Area Selected</span>
            </div>
            <span className="text-white text-sm font-medium">
              {(() => {
                const coords = coordinateString.split(',').map(c => parseFloat(c.trim()));
                if (coords.length === 4) {
                  const [minLat, minLng, maxLat, maxLng] = coords;
                  return calculateArea([minLng, minLat, maxLng, maxLat]).toFixed(2);
                }
                return '0';
              })()} km²
            </span>
          </div>
        )}
        </div>
    </div>
  );
};

export default AOIMapDrawer;