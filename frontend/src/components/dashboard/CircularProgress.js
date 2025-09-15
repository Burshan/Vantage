import React, { useState, useEffect } from 'react';

const CircularProgress = ({ 
  percentage, 
  size = 120, 
  strokeWidth = 8, 
  color = 'blue',
  showPercentage = true,
  title,
  subtitle,
  animated = true 
}) => {
  const [animatedPercentage, setAnimatedPercentage] = useState(0);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    setIsVisible(true);
    if (animated) {
      let start = 0;
      const end = percentage;
      const duration = 2500;
      const increment = end / (duration / 16);
      
      const timer = setInterval(() => {
        start += increment;
        if (start >= end) {
          setAnimatedPercentage(end);
          clearInterval(timer);
        } else {
          setAnimatedPercentage(start);
        }
      }, 16);
      
      return () => clearInterval(timer);
    } else {
      setAnimatedPercentage(percentage);
    }
  }, [percentage, animated]);

  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDasharray = circumference;
  const strokeDashoffset = circumference - (animatedPercentage / 100) * circumference;

  const colorClasses = {
    blue: {
      primary: '#3B82F6',
      secondary: '#1E40AF',
      background: '#1E293B',
      text: '#3B82F6',
      glow: '0 0 20px rgba(59, 130, 246, 0.4)'
    },
    emerald: {
      primary: '#10B981',
      secondary: '#047857',
      background: '#1E293B',
      text: '#10B981',
      glow: '0 0 20px rgba(16, 185, 129, 0.4)'
    },
    amber: {
      primary: '#F59E0B',
      secondary: '#D97706',
      background: '#1E293B',
      text: '#F59E0B',
      glow: '0 0 20px rgba(245, 158, 11, 0.4)'
    },
    red: {
      primary: '#EF4444',
      secondary: '#DC2626',
      background: '#1E293B',
      text: '#EF4444',
      glow: '0 0 20px rgba(239, 68, 68, 0.4)'
    },
    purple: {
      primary: '#8B5CF6',
      secondary: '#7C3AED',
      background: '#1E293B',
      text: '#8B5CF6',
      glow: '0 0 20px rgba(139, 92, 246, 0.4)'
    }
  };

  const colors = colorClasses[color] || colorClasses.blue;

  return (
    <div className={`
      flex flex-col items-center space-y-4
      transition-all duration-1000 ease-out
      ${isVisible ? 'opacity-100 transform scale-100' : 'opacity-0 transform scale-90'}
    `}>
      <div className="relative">
        <svg
          width={size}
          height={size}
          className="transform -rotate-90 drop-shadow-lg"
          style={{ filter: `drop-shadow(${colors.glow})` }}
        >
          <defs>
            <linearGradient id={`gradient-${color}`} x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor={colors.primary} />
              <stop offset="100%" stopColor={colors.secondary} />
            </linearGradient>
            
            <filter id={`glow-${color}`}>
              <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
              <feMerge> 
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
              </feMerge>
            </filter>
          </defs>

          {/* Background circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke={colors.background}
            strokeWidth={strokeWidth}
            fill="transparent"
            opacity="0.2"
          />

          {/* Progress circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke={`url(#gradient-${color})`}
            strokeWidth={strokeWidth}
            fill="transparent"
            strokeDasharray={strokeDasharray}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            className="transition-all duration-1000 ease-out"
            filter={`url(#glow-${color})`}
            style={{
              transformOrigin: `${size / 2}px ${size / 2}px`,
            }}
          />

          {/* Animated dots along the progress */}
          {animatedPercentage > 0 && (
            <circle
              cx={size / 2 + radius * Math.cos((animatedPercentage / 100) * 2 * Math.PI - Math.PI / 2)}
              cy={size / 2 + radius * Math.sin((animatedPercentage / 100) * 2 * Math.PI - Math.PI / 2)}
              r="4"
              fill={colors.primary}
              className="animate-pulse"
              filter={`url(#glow-${color})`}
            />
          )}
        </svg>

        {/* Center content */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          {showPercentage && (
            <div 
              className="text-2xl font-light text-white mb-1"
              style={{ color: colors.text }}
            >
              {Math.round(animatedPercentage)}%
            </div>
          )}
          {title && (
            <div className="text-xs font-medium text-slate-300 text-center uppercase tracking-wide">
              {title}
            </div>
          )}
          {subtitle && (
            <div className="text-xs text-slate-500 text-center mt-1">
              {subtitle}
            </div>
          )}
        </div>

        {/* Pulse effect */}
        <div 
          className="absolute inset-0 rounded-full animate-ping opacity-20"
          style={{ 
            background: `radial-gradient(circle, ${colors.primary}20 0%, transparent 70%)`,
            animation: 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite'
          }}
        />
      </div>
    </div>
  );
};

export default CircularProgress;