'use client';

import React from 'react';
import { useTheme } from '@/lib/ThemeContext';

export function DeskLampToggle() {
  const { theme, toggleTheme } = useTheme();
  const isLight = theme === 'light';

  return (
    <button
      type="button"
      onClick={toggleTheme}
      aria-label={`Switch to ${isLight ? 'Night desk' : 'Day desk'}`}
      className="inline-flex items-center gap-2 px-3 py-1.5 rounded border cursor-pointer select-none text-xs font-mono font-medium hover:opacity-80"
      style={{
        backgroundColor: 'var(--bg-elevated)',
        borderColor: 'var(--border-subtle)',
        color: 'var(--text-secondary)',
      }}
    >
      <span className="text-[11px] tracking-tight" style={{ color: 'var(--text-muted)' }}>
        {isLight ? 'Day desk' : 'Night desk'}
      </span>
      {/* Sliding Knob */}
      <div
        className="w-8 h-4 rounded-full relative p-0.5 flex items-center flex-shrink-0"
        style={{ backgroundColor: 'var(--border-med)' }}
      >
        <div
          className="w-3 h-3 rounded-full shadow-sm"
          style={{
            backgroundColor: 'var(--switch-knob)',
            transform: isLight ? 'translateX(16px)' : 'translateX(0px)',
            transition: 'transform 0.2s ease',
          }}
        />
      </div>
    </button>
  );
}
