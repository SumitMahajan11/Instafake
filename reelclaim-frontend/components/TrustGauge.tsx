'use client';

import React, { useEffect, useState } from 'react';

interface TrustGaugeProps {
  score: number | null;
  label?: string;
  size?: number;
  strokeWidth?: number;
  status?: string | null;
}

export const TrustGauge: React.FC<TrustGaugeProps> = ({
  score,
  label = 'Trust Score',
  size = 80,
  strokeWidth = 6,
  status,
}) => {
  const [animatedScore, setAnimatedScore] = useState<number>(0);

  const radius = (size - strokeWidth * 2) / 2;
  const circumference = 2 * Math.PI * radius;

  useEffect(() => {
    if (score !== null && score !== undefined) {
      // Trigger smooth 0.8s transition on mount / score change
      const timer = setTimeout(() => {
        setAnimatedScore(score);
      }, 50);
      return () => clearTimeout(timer);
    } else {
      setAnimatedScore(0);
    }
  }, [score]);

  // Determine stroke color based on status or score ranges
  const getStrokeColor = (): string => {
    if (status === 'blocked' || status === 'failed') {
      return 'var(--verdict-false-text)';
    }
    if (status === 'degraded' || status === 'busy') {
      return 'var(--verdict-misleading-text)';
    }
    if (score === null || score === undefined) {
      return 'var(--verdict-unverified-text)';
    }
    if (score >= 80) return 'var(--verdict-verified-text)';
    if (score >= 40) return 'var(--verdict-misleading-text)';
    return 'var(--verdict-false-text)';
  };

  const strokeColor = getStrokeColor();
  const strokeDashoffset = circumference - (animatedScore / 100) * circumference;

  return (
    <div className="flex items-center gap-3.5 select-none">
      {/* Circular SVG Gauge */}
      <div
        className="relative flex items-center justify-center"
        style={{ width: size, height: size }}
      >
        <svg
          width={size}
          height={size}
          className="transform -rotate-90 overflow-visible"
        >
          {/* Track Circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke="var(--bg-elevated)"
            strokeWidth={strokeWidth}
            fill="transparent"
          />
          {/* Animated Gauge Ring */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke={strokeColor}
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={score !== null ? strokeDashoffset : circumference}
            strokeLinecap="round"
            fill="transparent"
            style={{
              transition: 'stroke-dashoffset 0.8s ease-out, stroke 0.3s ease',
            }}
          />
        </svg>

        {/* Center Percentage Display */}
        <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
          {score !== null && score !== undefined ? (
            <span
              className="font-black tracking-tight text-base sm:text-lg"
              style={{ color: 'var(--text-primary)' }}
            >
              {animatedScore}%
            </span>
          ) : (
            <span
              className="font-mono text-xs font-bold uppercase"
              style={{ color: 'var(--text-muted)' }}
            >
              N/A
            </span>
          )}
        </div>
      </div>

      {/* Label and Status */}
      <div className="space-y-0.5">
        <div
          className="text-[10px] font-mono uppercase tracking-wider font-semibold"
          style={{ color: 'var(--text-muted)' }}
        >
          {label}
        </div>
        <div
          className="text-xs font-bold tracking-tight"
          style={{ color: strokeColor }}
        >
          {score !== null && score !== undefined
            ? score >= 80
              ? 'High Trust'
              : score >= 40
              ? 'Partial Trust'
              : 'Low Trust'
            : 'Unverified'}
        </div>
      </div>
    </div>
  );
};
