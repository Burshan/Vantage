import React, { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, Activity, Zap } from 'lucide-react';

const LiveChart = ({ 
  title, 
  data = [], 
  color = 'blue',
  type = 'line',
  showTrend = true,
  height = 200,
  animated = true 
}) => {
  const [animatedData, setAnimatedData] = useState([]);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    setIsVisible(true);
    if (animated && data.length > 0) {
      // Much faster animation - show all data quickly
      setAnimatedData([]);
      setTimeout(() => {
        setAnimatedData(data);
      }, 100); // Just a brief delay, then show everything
    } else {
      setAnimatedData(data);
    }
  }, [data, animated]);

  const maxValue = Math.max(...data.map(d => d.value), 1);
  const minValue = Math.min(...data.map(d => d.value), 0);
  const range = maxValue - minValue || 1;

  const colorClasses = {
    blue: {
      gradient: 'from-blue-500/20 via-blue-400/10 to-transparent',
      stroke: 'stroke-blue-400',
      dot: 'fill-blue-400',
      glow: 'drop-shadow-[0_0_8px_rgba(59,130,246,0.6)]'
    },
    emerald: {
      gradient: 'from-emerald-500/20 via-emerald-400/10 to-transparent',
      stroke: 'stroke-emerald-400',
      dot: 'fill-emerald-400',
      glow: 'drop-shadow-[0_0_8px_rgba(16,185,129,0.6)]'
    },
    amber: {
      gradient: 'from-amber-500/20 via-amber-400/10 to-transparent',
      stroke: 'stroke-amber-400',
      dot: 'fill-amber-400',
      glow: 'drop-shadow-[0_0_8px_rgba(245,158,11,0.6)]'
    },
    red: {
      gradient: 'from-red-500/20 via-red-400/10 to-transparent',
      stroke: 'stroke-red-400',
      dot: 'fill-red-400',
      glow: 'drop-shadow-[0_0_8px_rgba(239,68,68,0.6)]'
    }
  };

  const colors = colorClasses[color] || colorClasses.blue;

  const generatePath = (points) => {
    if (points.length === 0) return '';
    
    const width = 400;
    const stepX = width / (points.length - 1 || 1);
    
    let path = '';
    points.forEach((point, index) => {
      const x = index * stepX;
      const y = height - ((point.value - minValue) / range) * (height - 40);
      
      if (index === 0) {
        path += `M ${x} ${y}`;
      } else {
        const prevX = (index - 1) * stepX;
        const prevY = height - ((points[index - 1].value - minValue) / range) * (height - 40);
        const cpX1 = prevX + stepX * 0.4;
        const cpX2 = x - stepX * 0.4;
        path += ` C ${cpX1} ${prevY} ${cpX2} ${y} ${x} ${y}`;
      }
    });
    
    return path;
  };

  const generateAreaPath = (points) => {
    if (points.length === 0) return '';
    
    const linePath = generatePath(points);
    const width = 400;
    const stepX = width / (points.length - 1 || 1);
    const lastX = (points.length - 1) * stepX;
    
    return `${linePath} L ${lastX} ${height} L 0 ${height} Z`;
  };

  const calculateTrend = () => {
    if (data.length < 2) return { direction: 'neutral', percentage: 0 };
    
    const recent = data.slice(-5);
    const firstValue = recent[0].value;
    const lastValue = recent[recent.length - 1].value;
    const percentage = ((lastValue - firstValue) / firstValue) * 100;
    
    return {
      direction: percentage > 2 ? 'up' : percentage < -2 ? 'down' : 'neutral',
      percentage: Math.abs(percentage)
    };
  };

  const trend = calculateTrend();

  return (
    <div className={`transition-all duration-1000 ${isVisible ? 'opacity-100 transform translate-y-0' : 'opacity-0 transform translate-y-4'}`}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <h3 className="text-sm font-medium text-white tracking-wide">{title}</h3>
          <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse"></div>
        </div>
        
        {showTrend && data.length > 1 && (
          <div className={`flex items-center space-x-1 text-xs font-medium ${
            trend.direction === 'up' ? 'text-emerald-400' :
            trend.direction === 'down' ? 'text-red-400' : 'text-slate-400'
          }`}>
            {trend.direction === 'up' ? <TrendingUp className="w-3 h-3" /> :
             trend.direction === 'down' ? <TrendingDown className="w-3 h-3" /> :
             <Activity className="w-3 h-3" />}
            <span>{trend.percentage.toFixed(1)}%</span>
          </div>
        )}
      </div>

      <div className="relative">
        <svg 
          width="100%" 
          height={height} 
          viewBox={`0 0 400 ${height}`}
          className="overflow-visible"
        >
          <defs>
            <linearGradient id={`gradient-${color}`} x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" className="stop-opacity-30" style={{stopColor: `rgb(${color === 'blue' ? '59, 130, 246' : color === 'emerald' ? '16, 185, 129' : color === 'amber' ? '245, 158, 11' : '239, 68, 68'})`}} />
              <stop offset="100%" className="stop-opacity-0" style={{stopColor: `rgb(${color === 'blue' ? '59, 130, 246' : color === 'emerald' ? '16, 185, 129' : color === 'amber' ? '245, 158, 11' : '239, 68, 68'})`}} />
            </linearGradient>
            
            <filter id={`glow-${color}`}>
              <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
              <feMerge> 
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
              </feMerge>
            </filter>
          </defs>

          {/* Grid lines */}
          {[...Array(5)].map((_, i) => (
            <line
              key={i}
              x1="0"
              y1={(height / 4) * i}
              x2="400"
              y2={(height / 4) * i}
              stroke="rgb(51, 65, 85)"
              strokeWidth="0.5"
              opacity="0.3"
            />
          ))}

          {/* Area fill */}
          <path
            d={generateAreaPath(animatedData)}
            fill={`url(#gradient-${color})`}
            className="opacity-40"
          />

          {/* Line */}
          <path
            d={generatePath(animatedData)}
            fill="none"
            stroke={`rgb(${color === 'blue' ? '59, 130, 246' : color === 'emerald' ? '16, 185, 129' : color === 'amber' ? '245, 158, 11' : '239, 68, 68'})`}
            strokeWidth="2"
            filter={`url(#glow-${color})`}
            className="transition-all duration-300"
          />

          {/* Data points */}
          {animatedData.map((point, index) => {
            const width = 400;
            const stepX = width / (animatedData.length - 1 || 1);
            const x = index * stepX;
            const y = height - ((point.value - minValue) / range) * (height - 40);
            
            return (
              <g key={index}>
                <circle
                  cx={x}
                  cy={y}
                  r="3"
                  fill={`rgb(${color === 'blue' ? '59, 130, 246' : color === 'emerald' ? '16, 185, 129' : color === 'amber' ? '245, 158, 11' : '239, 68, 68'})`}
                  className="animate-pulse"
                  filter={`url(#glow-${color})`}
                />
                <circle
                  cx={x}
                  cy={y}
                  r="6"
                  fill="none"
                  stroke={`rgb(${color === 'blue' ? '59, 130, 246' : color === 'emerald' ? '16, 185, 129' : color === 'amber' ? '245, 158, 11' : '239, 68, 68'})`}
                  strokeWidth="1"
                  opacity="0.3"
                  className="animate-ping"
                />
              </g>
            );
          })}
        </svg>

        {/* Value indicators */}
        {data.length > 0 && (
          <div className="absolute top-2 right-2 bg-slate-800/80 backdrop-blur-sm border border-slate-600/30 rounded-lg px-3 py-1.5">
            <div className="text-xs text-slate-400 mb-0.5">Current</div>
            <div className={`text-sm font-bold ${colors.stroke.replace('stroke-', 'text-')}`}>
              {data[data.length - 1]?.value?.toFixed(1)}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default LiveChart;