import React, { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, Minus, Activity } from 'lucide-react';

const MetricCard = ({ 
  title, 
  value, 
  previousValue, 
  icon: Icon, 
  color = 'blue',
  suffix = '',
  animated = true,
  size = 'normal'
}) => {
  const [displayValue, setDisplayValue] = useState(animated ? 0 : value);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    setIsVisible(true);
    if (animated && typeof value === 'number') {
      // Much faster animation - 300ms instead of 2000ms
      let start = Math.max(0, value - 5); // Start closer to end value
      const end = value;
      const duration = 300;
      const increment = (end - start) / (duration / 50); // Larger steps, less frequent updates
      
      const timer = setInterval(() => {
        start += increment;
        if (start >= end) {
          setDisplayValue(end);
          clearInterval(timer);
        } else {
          setDisplayValue(Math.floor(start));
        }
      }, 50); // Less frequent updates
      
      return () => clearInterval(timer);
    } else {
      setDisplayValue(value);
    }
  }, [value, animated]);

  const calculateChange = () => {
    if (typeof value !== 'number' || typeof previousValue !== 'number' || previousValue === 0) {
      return { percentage: 0, direction: 'neutral' };
    }
    
    const change = ((value - previousValue) / previousValue) * 100;
    return {
      percentage: Math.abs(change),
      direction: change > 2 ? 'up' : change < -2 ? 'down' : 'neutral'
    };
  };

  const change = calculateChange();

  const colorClasses = {
    blue: {
      bg: 'from-blue-500/10 to-blue-600/5',
      border: 'border-blue-500/20',
      icon: 'text-blue-400',
      iconBg: 'bg-blue-500/20',
      glow: 'shadow-blue-500/20',
      value: 'text-white',
      pulse: 'bg-blue-400'
    },
    emerald: {
      bg: 'from-emerald-500/10 to-emerald-600/5',
      border: 'border-emerald-500/20',
      icon: 'text-emerald-400',
      iconBg: 'bg-emerald-500/20',
      glow: 'shadow-emerald-500/20',
      value: 'text-white',
      pulse: 'bg-emerald-400'
    },
    amber: {
      bg: 'from-amber-500/10 to-amber-600/5',
      border: 'border-amber-500/20',
      icon: 'text-amber-400',
      iconBg: 'bg-amber-500/20',
      glow: 'shadow-amber-500/20',
      value: 'text-white',
      pulse: 'bg-amber-400'
    },
    red: {
      bg: 'from-red-500/10 to-red-600/5',
      border: 'border-red-500/20',
      icon: 'text-red-400',
      iconBg: 'bg-red-500/20',
      glow: 'shadow-red-500/20',
      value: 'text-white',
      pulse: 'bg-red-400'
    },
    purple: {
      bg: 'from-purple-500/10 to-purple-600/5',
      border: 'border-purple-500/20',
      icon: 'text-purple-400',
      iconBg: 'bg-purple-500/20',
      glow: 'shadow-purple-500/20',
      value: 'text-white',
      pulse: 'bg-purple-400'
    }
  };

  const colors = colorClasses[color] || colorClasses.blue;
  const sizeClasses = size === 'large' ? 'p-8' : 'p-6';

  return (
    <div className={`
      relative overflow-hidden
      bg-gradient-to-br ${colors.bg} backdrop-blur-xl
      border ${colors.border}
      rounded-2xl ${sizeClasses}
      hover:border-opacity-40 hover:shadow-xl
      transition-all duration-200 ease-out
      group cursor-pointer
      ${isVisible ? 'opacity-100' : 'opacity-0'}
    `}>
      {/* Simple background gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-white/3 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-200" />
      
      <div className="relative z-10">
        <div className="flex items-center justify-between mb-4">
          <div className={`p-3 ${colors.iconBg} rounded-xl backdrop-blur-sm group-hover:scale-105 transition-transform duration-150`}>
            {Icon && <Icon className={`w-5 h-5 ${colors.icon}`} />}
          </div>
          
          {change.direction !== 'neutral' && (
            <div className={`flex items-center space-x-1 px-2 py-1 rounded-full text-xs font-medium backdrop-blur-sm ${
              change.direction === 'up' 
                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' 
                : 'bg-red-500/20 text-red-400 border border-red-500/30'
            }`}>
              {change.direction === 'up' ? (
                <TrendingUp className="w-3 h-3" />
              ) : (
                <TrendingDown className="w-3 h-3" />
              )}
              <span>{change.percentage.toFixed(1)}%</span>
            </div>
          )}
        </div>

        <div className="space-y-2">
          <div className={`text-3xl font-light ${colors.value} tracking-tight group-hover:scale-105 transition-transform duration-300`}>
            {typeof displayValue === 'number' ? displayValue.toLocaleString() : displayValue}
            {suffix && <span className="text-lg text-slate-400 ml-1">{suffix}</span>}
          </div>
          
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-medium text-slate-400 tracking-wide uppercase">
              {title}
            </h3>
            
            {/* Live indicator */}
            <div className="flex items-center space-x-2">
              <div className={`w-2 h-2 ${colors.pulse} rounded-full animate-pulse`} />
              <span className="text-xs text-slate-500 font-medium">LIVE</span>
            </div>
          </div>
        </div>

        {/* Bottom accent line */}
        <div className={`absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r ${colors.bg} opacity-50 group-hover:opacity-100 transition-opacity duration-300`} />
      </div>
    </div>
  );
};

export default MetricCard;