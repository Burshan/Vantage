import React, { useState, useEffect, useRef } from 'react';
import { ZoomIn, ZoomOut, Square, Move, Trash2, Satellite } from 'lucide-react';

const SatelliteMapDrawer = ({ onAOIChange, initialBounds = null, className = "" }) => {
  const mapRef = useRef(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [drawStart, setDrawStart] = useState(null);
  const [drawEnd, setDrawEnd] = useState(null);
  const [aoiBox, setAoiBox] = useState(null);
  const [zoom, setZoom] = useState(4);
  const [center, setCenter] = useState([39.8283, -98.5795]); // Center US
  const [tileUrl, setTileUrl] = useState('');
  
  // Convert lat/lng to pixel position
  const latLngToPixel = (lat, lng, mapWidth, mapHeight, mapCenter, mapZoom) => {
    const scale = Math.pow(2, mapZoom);
    const worldWidth = 256 * scale;
    const worldHeight = 256 * scale;
    
    const x = (lng + 180) * (worldWidth / 360);
    const y = (1 - Math.log(Math.tan(lat * Math.PI / 180) + 1 / Math.cos(lat * Math.PI / 180)) / Math.PI) / 2 * worldHeight;
    
    const centerX = (mapCenter[1] + 180) * (worldWidth / 360);
    const centerY = (1 - Math.log(Math.tan(mapCenter[0] * Math.PI / 180) + 1 / Math.cos(mapCenter[0] * Math.PI / 180)) / Math.PI) / 2 * worldHeight;
    
    return [
      x - centerX + mapWidth / 2,
      y - centerY + mapHeight / 2
    ];
  };
  
  // Convert pixel position to lat/lng
  const pixelToLatLng = (x, y, mapWidth, mapHeight, mapCenter, mapZoom) => {
    const scale = Math.pow(2, mapZoom);
    const worldWidth = 256 * scale;
    const worldHeight = 256 * scale;
    
    const centerX = (mapCenter[1] + 180) * (worldWidth / 360);
    const centerY = (1 - Math.log(Math.tan(mapCenter[0] * Math.PI / 180) + 1 / Math.cos(mapCenter[0] * Math.PI / 180)) / Math.PI) / 2 * worldHeight;
    
    const worldX = x + centerX - mapWidth / 2;
    const worldY = y + centerY - mapHeight / 2;
    
    const lng = (worldX / worldWidth) * 360 - 180;
    const n = Math.PI - 2 * Math.PI * worldY / worldHeight;
    const lat = (180 / Math.PI) * Math.atan(0.5 * (Math.exp(n) - Math.exp(-n)));
    
    return [lat, lng];
  };

  // Generate tile URL for satellite imagery
  const generateTileUrl = (lat, lng, zoomLevel) => {
    // Use multiple satellite imagery sources for better reliability
    const sources = [
      'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      'https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
      'https://services.arcgisonline.com/arcgis/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
    ];
    
    // Calculate tile coordinates
    const n = Math.pow(2, zoomLevel);
    const x = Math.floor(((lng + 180) / 360) * n);
    const y = Math.floor((1 - Math.log(Math.tan(lat * Math.PI / 180) + 1 / Math.cos(lat * Math.PI / 180)) / Math.PI) / 2 * n);
    
    // Use Google satellite tiles as primary (more reliable)
    return `https://mt1.google.com/vt/lyrs=s&x=${x}&y=${y}&z=${zoomLevel}`;
  };

  // Initialize map
  useEffect(() => {
    if (!mapRef.current) return;
    
    const currentTileUrl = generateTileUrl(center[0], center[1], zoom);
    setTileUrl(currentTileUrl);
    
    // Create the map HTML structure with simplified, reliable implementation
    mapRef.current.innerHTML = `
      <div style="
        width: 100%; 
        height: 100%; 
        background: #1e293b;
        background-image: url('${currentTileUrl}');
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        position: relative;
        cursor: crosshair;
        border-radius: 0.5rem;
        overflow: hidden;
      " id="satellite-map">
        ${aoiBox ? `
          <div style="
            position: absolute;
            border: 2px solid #3B82F6;
            background: rgba(59, 130, 246, 0.3);
            left: ${Math.min(aoiBox.start[0], aoiBox.end[0])}px;
            top: ${Math.min(aoiBox.start[1], aoiBox.end[1])}px;
            width: ${Math.abs(aoiBox.end[0] - aoiBox.start[0])}px;
            height: ${Math.abs(aoiBox.end[1] - aoiBox.start[1])}px;
            pointer-events: none;
            box-shadow: 0 0 10px rgba(59, 130, 246, 0.5);
          "></div>
        ` : ''}
        ${isDrawing && drawStart && drawEnd ? `
          <div style="
            position: absolute;
            border: 2px dashed #10B981;
            background: rgba(16, 185, 129, 0.3);
            left: ${Math.min(drawStart[0], drawEnd[0])}px;
            top: ${Math.min(drawStart[1], drawEnd[1])}px;
            width: ${Math.abs(drawEnd[0] - drawStart[0])}px;
            height: ${Math.abs(drawEnd[1] - drawStart[1])}px;
            pointer-events: none;
            box-shadow: 0 0 8px rgba(16, 185, 129, 0.4);
          "></div>
        ` : ''}
      </div>
    `;
    
    const mapElement = mapRef.current.querySelector('#satellite-map');
    
    // Mouse event handlers
    const handleMouseDown = (e) => {
      const rect = mapElement.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      setDrawStart([x, y]);
      setIsDrawing(true);
    };
    
    const handleMouseMove = (e) => {
      if (!isDrawing) return;
      const rect = mapElement.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      setDrawEnd([x, y]);
    };
    
    const handleMouseUp = (e) => {
      if (!isDrawing || !drawStart) return;
      
      const rect = mapElement.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      
      const finalBox = {
        start: drawStart,
        end: [x, y]
      };
      
      // Convert to lat/lng
      const startLatLng = pixelToLatLng(
        finalBox.start[0], finalBox.start[1], 
        rect.width, rect.height, center, zoom
      );
      const endLatLng = pixelToLatLng(
        finalBox.end[0], finalBox.end[1], 
        rect.width, rect.height, center, zoom
      );
      
      const bounds = {
        minLat: Math.min(startLatLng[0], endLatLng[0]),
        maxLat: Math.max(startLatLng[0], endLatLng[0]),
        minLng: Math.min(startLatLng[1], endLatLng[1]),
        maxLng: Math.max(startLatLng[1], endLatLng[1])
      };
      
      // Calculate area
      const R = 6371;
      const dLat = (bounds.maxLat - bounds.minLat) * Math.PI / 180;
      const dLng = (bounds.maxLng - bounds.minLng) * Math.PI / 180;
      const lat1 = bounds.minLat * Math.PI / 180;
      const lat2 = bounds.maxLat * Math.PI / 180;
      const width = R * Math.cos((lat1 + lat2) / 2) * dLng;
      const height = R * dLat;
      const area = Math.abs(width * height);
      
      setAoiBox(finalBox);
      setIsDrawing(false);
      setDrawStart(null);
      setDrawEnd(null);
      
      if (onAOIChange) {
        onAOIChange({
          bbox: [bounds.minLng, bounds.minLat, bounds.maxLng, bounds.maxLat],
          area,
          type: 'rectangle',
          isValid: true
        });
      }
    };
    
    mapElement.addEventListener('mousedown', handleMouseDown);
    mapElement.addEventListener('mousemove', handleMouseMove);
    mapElement.addEventListener('mouseup', handleMouseUp);
    mapElement.addEventListener('mouseleave', handleMouseUp);
    
    return () => {
      if (mapElement) {
        mapElement.removeEventListener('mousedown', handleMouseDown);
        mapElement.removeEventListener('mousemove', handleMouseMove);
        mapElement.removeEventListener('mouseup', handleMouseUp);
        mapElement.removeEventListener('mouseleave', handleMouseUp);
      }
    };
  }, [zoom, center, aoiBox, isDrawing, drawStart, drawEnd]);
  
  // Load initial bounds
  useEffect(() => {
    if (initialBounds && initialBounds.length === 4) {
      const [minLng, minLat, maxLng, maxLat] = initialBounds;
      const centerLat = (minLat + maxLat) / 2;
      const centerLng = (minLng + maxLng) / 2;
      setCenter([centerLat, centerLng]);
      setZoom(8);
    }
  }, [initialBounds]);
  
  const handleZoomIn = () => setZoom(Math.min(18, zoom + 1));
  const handleZoomOut = () => setZoom(Math.max(1, zoom - 1));
  
  const clearAOI = () => {
    setAoiBox(null);
    if (onAOIChange) {
      onAOIChange({
        bbox: null,
        area: 0,
        type: null,
        isValid: false
      });
    }
  };
  
  return (
    <div className={className}>
      <div className="bg-slate-700 rounded-lg p-4 h-[400px] flex flex-col">
        {/* Controls */}
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-sm font-semibold text-white flex items-center">
            <Satellite className="w-4 h-4 mr-2 text-blue-400" />
            Satellite Imagery Map
          </h3>
          <div className="flex items-center space-x-2">
            <button
              onClick={handleZoomIn}
              className="p-1 bg-slate-600 hover:bg-slate-500 text-white rounded transition-colors"
              title="Zoom in"
            >
              <ZoomIn className="w-4 h-4" />
            </button>
            <button
              onClick={handleZoomOut}
              className="p-1 bg-slate-600 hover:bg-slate-500 text-white rounded transition-colors"
              title="Zoom out"
            >
              <ZoomOut className="w-4 h-4" />
            </button>
            <span className="text-xs text-gray-400 px-2">Z: {zoom}</span>
            {aoiBox && (
              <button
                onClick={clearAOI}
                className="p-1 bg-red-600 hover:bg-red-500 text-white rounded transition-colors"
                title="Clear AOI"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
        
        {/* Map Container */}
        <div className="flex-1 relative border border-slate-600 rounded overflow-hidden">
          <div ref={mapRef} className="w-full h-full" />
          
          {/* Instructions */}
          <div className="absolute top-2 left-2 bg-black bg-opacity-75 rounded px-2 py-1">
            <div className="text-xs text-white flex items-center">
              <Square className="w-3 h-3 mr-1 text-green-400" />
              Click & drag to select AOI
            </div>
          </div>
          
          {/* AOI info */}
          {aoiBox && (
            <div className="absolute top-2 right-2 bg-black bg-opacity-90 rounded-lg px-3 py-2 border border-blue-500">
              <div className="text-xs text-white space-y-1">
                <div className="font-semibold text-blue-400 flex items-center">
                  <Square className="w-3 h-3 mr-1" />
                  AOI Selected
                </div>
                <div className="text-green-300">✓ Ready for analysis</div>
                <div className="text-gray-300">Satellite view • Z{zoom}</div>
              </div>
            </div>
          )}
        </div>
        
        <div className="mt-2 text-xs text-gray-400 text-center">
          🛰️ High-resolution satellite imagery • Click and drag to create AOI rectangle
        </div>
      </div>
    </div>
  );
};

export default SatelliteMapDrawer;