import React, { useState } from 'react';
import { X, ChevronLeft, ChevronRight, Play, Pause, TrendingUp, Calendar, RotateCcw } from 'lucide-react';
import { buildImageURL } from '../../config/api';

const TrendGallery = ({ analyses, isOpen, onClose, aoi }) => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playSpeed, setPlaySpeed] = useState(1000); // ms between frames
  const [playInterval, setPlayInterval] = useState(null);

  if (!isOpen || !analyses || analyses.length === 0) return null;

  // Sort analyses by date (oldest first for trend visualization)
  const sortedAnalyses = [...analyses].sort((a, b) => 
    new Date(a.analysis_timestamp) - new Date(b.analysis_timestamp)
  );

  // Filter only analyses that have current images
  const trendImages = sortedAnalyses
    .filter(analysis => analysis.images?.current_url)
    .map((analysis, index) => ({
      url: analysis.images.current_url,
      title: `Analysis ${index + 1}`,
      date: new Date(analysis.analysis_timestamp),
      change: analysis.change_percentage,
      analysis_id: analysis.id,
      operation: analysis.operation_name
    }));

  const currentImage = trendImages[currentIndex];

  const handlePrevious = () => {
    setCurrentIndex(prev => prev > 0 ? prev - 1 : trendImages.length - 1);
  };

  const handleNext = () => {
    setCurrentIndex(prev => prev < trendImages.length - 1 ? prev + 1 : 0);
  };

  const startSlideshow = () => {
    if (playInterval) return;
    
    setIsPlaying(true);
    const interval = setInterval(() => {
      setCurrentIndex(prev => {
        if (prev < trendImages.length - 1) {
          return prev + 1;
        } else {
          // Loop back to start
          return 0;
        }
      });
    }, playSpeed);
    setPlayInterval(interval);
  };

  const stopSlideshow = () => {
    if (playInterval) {
      clearInterval(playInterval);
      setPlayInterval(null);
    }
    setIsPlaying(false);
  };

  const resetToStart = () => {
    stopSlideshow();
    setCurrentIndex(0);
  };

  const handleKeyDown = (e) => {
    switch (e.key) {
      case 'Escape':
        stopSlideshow();
        onClose();
        break;
      case 'ArrowLeft':
        stopSlideshow();
        handlePrevious();
        break;
      case 'ArrowRight':
        stopSlideshow();
        handleNext();
        break;
      case ' ':
        e.preventDefault();
        isPlaying ? stopSlideshow() : startSlideshow();
        break;
      case 'r':
      case 'R':
        resetToStart();
        break;
      default:
        break;
    }
  };

  // Format date for display
  const formatDate = (date) => {
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric',
      year: 'numeric'
    });
  };

  // Get trend direction
  const getTrendDirection = () => {
    if (trendImages.length < 2) return null;
    const first = trendImages[0];
    const last = trendImages[trendImages.length - 1];
    return last.change > first.change ? 'increasing' : 'decreasing';
  };

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-95 z-50 flex items-center justify-center"
      onKeyDown={handleKeyDown}
      tabIndex={0}
    >
      {/* Header Controls */}
      <div className="absolute top-4 left-4 right-4 flex justify-between items-center z-10">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <TrendingUp className="w-6 h-6 text-blue-400" />
            <div>
              <h3 className="text-white font-bold text-lg">Trend Analysis: {aoi?.name}</h3>
              <p className="text-gray-400 text-sm">
                {trendImages.length} images • {currentIndex + 1} of {trendImages.length}
              </p>
            </div>
          </div>
          
          {getTrendDirection() && (
            <div className={`px-3 py-1 rounded-full text-xs font-semibold ${
              getTrendDirection() === 'increasing' 
                ? 'bg-red-500/20 text-red-300 border border-red-500/30' 
                : 'bg-green-500/20 text-green-300 border border-green-500/30'
            }`}>
              Change {getTrendDirection()}
            </div>
          )}
        </div>

        {/* Playback Controls */}
        <div className="flex items-center space-x-2">
          <button
            onClick={resetToStart}
            className="p-2 bg-black bg-opacity-50 text-white rounded hover:bg-opacity-70 transition-all"
            title="Reset to Start (R)"
          >
            <RotateCcw className="w-5 h-5" />
          </button>

          <select
            value={playSpeed}
            onChange={(e) => setPlaySpeed(parseInt(e.target.value))}
            className="bg-black bg-opacity-50 text-white text-sm px-2 py-1 rounded border border-gray-600"
          >
            <option value={500}>2x Speed</option>
            <option value={1000}>1x Speed</option>
            <option value={2000}>0.5x Speed</option>
            <option value={3000}>Slow</option>
          </select>

          <button
            onClick={isPlaying ? stopSlideshow : startSlideshow}
            className={`p-3 text-white rounded-full transition-all ${
              isPlaying 
                ? 'bg-red-500/80 hover:bg-red-600/80' 
                : 'bg-green-500/80 hover:bg-green-600/80'
            }`}
            title={isPlaying ? "Pause (Space)" : "Play Slideshow (Space)"}
          >
            {isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5" />}
          </button>

          <button
            onClick={() => {
              stopSlideshow();
              onClose();
            }}
            className="p-2 bg-black bg-opacity-50 text-white rounded hover:bg-opacity-70 transition-all"
            title="Close (Esc)"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Navigation Controls */}
      <button
        onClick={() => {
          stopSlideshow();
          handlePrevious();
        }}
        className="absolute left-4 top-1/2 transform -translate-y-1/2 p-3 bg-black bg-opacity-50 text-white rounded-full hover:bg-opacity-70 transition-all z-10"
        title="Previous Image (←)"
      >
        <ChevronLeft className="w-6 h-6" />
      </button>
      
      <button
        onClick={() => {
          stopSlideshow();
          handleNext();
        }}
        className="absolute right-4 top-1/2 transform -translate-y-1/2 p-3 bg-black bg-opacity-50 text-white rounded-full hover:bg-opacity-70 transition-all z-10"
        title="Next Image (→)"
      >
        <ChevronRight className="w-6 h-6" />
      </button>

      {/* Main Image */}
      <div className="flex-1 flex items-center justify-center p-16">
        {currentImage && (
          <div className="relative">
            <img
              src={currentImage.url.startsWith('http') ? currentImage.url : buildImageURL(currentImage.url.replace('/api/image/', ''))}
              alt={`Trend analysis ${currentIndex + 1}`}
              className="max-w-full max-h-full object-contain rounded-lg shadow-2xl"
              onLoad={() => {
                document.querySelector('[tabIndex="0"]')?.focus();
              }}
            />
            
            {/* Image Info Overlay */}
            <div className="absolute bottom-4 left-4 bg-black bg-opacity-75 text-white p-3 rounded-lg">
              <div className="flex items-center space-x-2 mb-2">
                <Calendar className="w-4 h-4" />
                <span className="text-sm font-semibold">{formatDate(currentImage.date)}</span>
              </div>
              <div className="text-xs text-gray-300">
                Change: {currentImage.change ? `${currentImage.change.toFixed(2)}%` : 'N/A'}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Timeline Strip */}
      <div className="absolute bottom-6 left-1/2 transform -translate-x-1/2 flex items-center bg-black bg-opacity-75 p-3 rounded-xl space-x-2">
        <span className="text-white text-sm mr-2">Timeline:</span>
        {trendImages.map((image, index) => (
          <button
            key={index}
            onClick={() => {
              stopSlideshow();
              setCurrentIndex(index);
            }}
            className={`relative group ${
              index === currentIndex 
                ? 'ring-2 ring-blue-400' 
                : ''
            }`}
          >
            <img
              src={image.url.startsWith('http') ? image.url : buildImageURL(image.url.replace('/api/image/', ''))}
              alt={`Trend ${index + 1}`}
              className={`w-12 h-12 object-cover rounded border-2 transition-all ${
                index === currentIndex 
                  ? 'border-blue-400 opacity-100' 
                  : 'border-gray-600 opacity-60 hover:opacity-80'
              }`}
            />
            {/* Tooltip */}
            <div className="absolute bottom-14 left-1/2 transform -translate-x-1/2 bg-black bg-opacity-90 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
              {formatDate(image.date)}
              <br />
              {image.change ? `${image.change.toFixed(1)}%` : 'N/A'}
            </div>
          </button>
        ))}
      </div>

      {/* Keyboard Shortcuts Help */}
      <div className="absolute top-20 right-4 bg-black bg-opacity-75 text-white p-3 rounded text-xs">
        <div className="text-gray-300 mb-1">Controls:</div>
        <div>← → : Navigate</div>
        <div>Space : Play/Pause</div>
        <div>R : Reset</div>
        <div>Esc : Close</div>
      </div>
    </div>
  );
};

export default TrendGallery;