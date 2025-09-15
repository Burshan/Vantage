import React, { useState } from 'react';
import { X, ChevronLeft, ChevronRight, ZoomIn, ZoomOut, RotateCcw } from 'lucide-react';
import { buildImageURL } from '../../config/api';

const ImageGallery = ({ images, isOpen, onClose, initialIndex = 0 }) => {
  const [currentIndex, setCurrentIndex] = useState(initialIndex);
  const [zoomLevel, setZoomLevel] = useState(1);
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [imageOffset, setImageOffset] = useState({ x: 0, y: 0 });

  if (!isOpen || !images || images.length === 0) return null;

  const currentImage = images[currentIndex];

  const handlePrevious = () => {
    setCurrentIndex(prev => prev > 0 ? prev - 1 : images.length - 1);
    resetImageView();
  };

  const handleNext = () => {
    setCurrentIndex(prev => prev < images.length - 1 ? prev + 1 : 0);
    resetImageView();
  };

  const handleZoomIn = () => {
    setZoomLevel(prev => Math.min(prev * 1.5, 5));
  };

  const handleZoomOut = () => {
    setZoomLevel(prev => Math.max(prev / 1.5, 0.5));
  };

  const resetImageView = () => {
    setZoomLevel(1);
    setImageOffset({ x: 0, y: 0 });
  };

  const handleMouseDown = (e) => {
    if (zoomLevel > 1) {
      setIsDragging(true);
      setDragStart({
        x: e.clientX - imageOffset.x,
        y: e.clientY - imageOffset.y
      });
    }
  };

  const handleMouseMove = (e) => {
    if (isDragging && zoomLevel > 1) {
      setImageOffset({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y
      });
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const handleKeyDown = (e) => {
    switch (e.key) {
      case 'Escape':
        onClose();
        break;
      case 'ArrowLeft':
        handlePrevious();
        break;
      case 'ArrowRight':
        handleNext();
        break;
      case '+':
      case '=':
        handleZoomIn();
        break;
      case '-':
        handleZoomOut();
        break;
      case '0':
        resetImageView();
        break;
      default:
        break;
    }
  };

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-90 z-50 flex items-center justify-center"
      onKeyDown={handleKeyDown}
      tabIndex={0}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
    >
      {/* Header Controls */}
      <div className="absolute top-4 left-4 right-4 flex justify-between items-center z-10">
        <div className="flex items-center space-x-2">
          <span className="text-white font-medium">
            {currentImage.title}
          </span>
          <span className="text-gray-400 text-sm">
            ({currentIndex + 1} of {images.length})
          </span>
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={handleZoomOut}
            disabled={zoomLevel <= 0.5}
            className="p-2 bg-black bg-opacity-50 text-white rounded hover:bg-opacity-70 disabled:opacity-50 transition-all"
            title="Zoom Out (-)"
          >
            <ZoomOut className="w-5 h-5" />
          </button>
          
          <span className="text-white text-sm min-w-[60px] text-center">
            {Math.round(zoomLevel * 100)}%
          </span>
          
          <button
            onClick={handleZoomIn}
            disabled={zoomLevel >= 5}
            className="p-2 bg-black bg-opacity-50 text-white rounded hover:bg-opacity-70 disabled:opacity-50 transition-all"
            title="Zoom In (+)"
          >
            <ZoomIn className="w-5 h-5" />
          </button>
          
          <button
            onClick={resetImageView}
            className="p-2 bg-black bg-opacity-50 text-white rounded hover:bg-opacity-70 transition-all"
            title="Reset View (0)"
          >
            <RotateCcw className="w-5 h-5" />
          </button>
          
          <button
            onClick={onClose}
            className="p-2 bg-black bg-opacity-50 text-white rounded hover:bg-opacity-70 transition-all"
            title="Close (Esc)"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Navigation Controls */}
      {images.length > 1 && (
        <>
          <button
            onClick={handlePrevious}
            className="absolute left-4 top-1/2 transform -translate-y-1/2 p-3 bg-black bg-opacity-50 text-white rounded-full hover:bg-opacity-70 transition-all z-10"
            title="Previous Image (←)"
          >
            <ChevronLeft className="w-6 h-6" />
          </button>
          
          <button
            onClick={handleNext}
            className="absolute right-4 top-1/2 transform -translate-y-1/2 p-3 bg-black bg-opacity-50 text-white rounded-full hover:bg-opacity-70 transition-all z-10"
            title="Next Image (→)"
          >
            <ChevronRight className="w-6 h-6" />
          </button>
        </>
      )}

      {/* Main Image */}
      <div className="flex-1 flex items-center justify-center p-16 overflow-hidden">
        <div 
          className="relative select-none"
          style={{
            transform: `scale(${zoomLevel}) translate(${imageOffset.x / zoomLevel}px, ${imageOffset.y / zoomLevel}px)`,
            cursor: zoomLevel > 1 ? (isDragging ? 'grabbing' : 'grab') : 'default',
            transition: isDragging ? 'none' : 'transform 0.2s ease-out'
          }}
          onMouseDown={handleMouseDown}
        >
          <img
            src={currentImage.url.startsWith('http') ? currentImage.url : buildImageURL(currentImage.url.replace('/api/image/', ''))}
            alt={currentImage.title}
            className="max-w-full max-h-full object-contain rounded-lg shadow-2xl"
            draggable={false}
            onLoad={() => {
              // Focus the container so keyboard shortcuts work
              document.querySelector('[tabIndex="0"]')?.focus();
            }}
          />
        </div>
      </div>

      {/* Image Description */}
      {currentImage.description && (
        <div className="absolute bottom-4 left-4 right-4 bg-black bg-opacity-75 text-white p-4 rounded-lg">
          <p className="text-sm">{currentImage.description}</p>
          {currentImage.metadata && (
            <div className="mt-2 text-xs text-gray-300 grid grid-cols-2 md:grid-cols-4 gap-2">
              {Object.entries(currentImage.metadata).map(([key, value]) => (
                <div key={key}>
                  <span className="font-medium">{key}:</span> {value}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Thumbnail Strip */}
      {images.length > 1 && (
        <div className="absolute bottom-20 left-1/2 transform -translate-x-1/2 flex space-x-2 bg-black bg-opacity-75 p-2 rounded-lg">
          {images.map((image, index) => (
            <button
              key={index}
              onClick={() => {
                setCurrentIndex(index);
                resetImageView();
              }}
              className={`w-12 h-12 rounded border-2 transition-all ${
                index === currentIndex 
                  ? 'border-blue-400 opacity-100' 
                  : 'border-gray-600 opacity-60 hover:opacity-80'
              }`}
            >
              <img
                src={image.url.startsWith('http') ? image.url : buildImageURL(image.url.replace('/api/image/', ''))}
                alt={image.title}
                className="w-full h-full object-cover rounded"
              />
            </button>
          ))}
        </div>
      )}

      {/* Keyboard Shortcuts Help */}
      <div className="absolute top-20 right-4 bg-black bg-opacity-75 text-white p-3 rounded text-xs">
        <div className="text-gray-300 mb-1">Keyboard Shortcuts:</div>
        <div>← → : Navigate</div>
        <div>+ - : Zoom</div>
        <div>0 : Reset</div>
        <div>Esc : Close</div>
      </div>
    </div>
  );
};

export default ImageGallery;