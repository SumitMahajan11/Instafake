import React from 'react';
import { AlertCircle, FileQuestion, ShieldAlert, RefreshCw } from 'lucide-react';

interface EmptyStateProps {
  type: 'zero_claims' | 'blocked_site' | 'network_error';
  message?: string;
  onReset?: () => void;
}

export const EmptyState: React.FC<EmptyStateProps> = ({ type, message, onReset }) => {
  if (type === 'zero_claims') {
    return (
      <div
        className="w-full rounded-xl p-8 text-center space-y-4 border shadow-sm"
        style={{
          backgroundColor: 'var(--bg-card)',
          borderColor: 'var(--border-subtle)',
          color: 'var(--text-primary)',
        }}
      >
        <div
          className="inline-flex p-3 rounded-full border"
          style={{
            backgroundColor: 'var(--bg-elevated)',
            borderColor: 'var(--border-med)',
            color: 'var(--text-muted)',
          }}
        >
          <FileQuestion className="w-6 h-6" />
        </div>
        <div className="space-y-1.5">
          <h3
            className="text-lg font-bold"
            style={{ fontFamily: 'var(--font-serif)', color: 'var(--text-primary)' }}
          >
            No Verifiable Claims Extracted
          </h3>
          <p className="text-xs max-w-md mx-auto leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
            The provided social caption did not contain explicit promotional claims (such as pricing, refunds, eligibility, or certificates).
          </p>
        </div>
        {onReset && (
          <button
            type="button"
            onClick={onReset}
            className="inline-flex items-center gap-2 px-4 py-2 rounded text-xs font-semibold border transition-all cursor-pointer hover:opacity-80"
            style={{
              backgroundColor: 'var(--bg-elevated)',
              borderColor: 'var(--border-bright)',
              color: 'var(--text-primary)',
              fontFamily: 'var(--font-mono)',
            }}
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Try Another Caption
          </button>
        )}
      </div>
    );
  }

  if (type === 'blocked_site') {
    return (
      <div
        className="w-full rounded-xl p-8 text-center space-y-4 border border-l-4 shadow-sm"
        style={{
          backgroundColor: 'var(--bg-card)',
          borderColor: 'var(--border-subtle)',
          borderLeftColor: 'var(--verdict-misleading-text)',
          color: 'var(--text-primary)',
        }}
      >
        <div
          className="inline-flex p-3 rounded-full border"
          style={{
            backgroundColor: 'var(--verdict-misleading-bg)',
            borderColor: 'var(--verdict-misleading-border)',
            color: 'var(--verdict-misleading-text)',
          }}
        >
          <ShieldAlert className="w-6 h-6" />
        </div>
        <div className="space-y-1.5">
          <h3
            className="text-lg font-bold"
            style={{ fontFamily: 'var(--font-serif)', color: 'var(--verdict-misleading-text)' }}
          >
            Could Not Verify Site — Proceed With Caution
          </h3>
          <p className="text-xs max-w-lg mx-auto leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
            {message || 'The target website blocked automated access (e.g. Cloudflare bot challenge or anti-scraping wall). Claims could not be cross-checked against published site pages.'}
          </p>
        </div>
        {onReset && (
          <button
            type="button"
            onClick={onReset}
            className="inline-flex items-center gap-2 px-4 py-2 rounded text-xs font-semibold border transition-all cursor-pointer hover:opacity-80"
            style={{
              backgroundColor: 'var(--bg-elevated)',
              borderColor: 'var(--border-med)',
              color: 'var(--text-primary)',
              fontFamily: 'var(--font-mono)',
            }}
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Audit Different URL
          </button>
        )}
      </div>
    );
  }

  return (
    <div
      className="w-full rounded-xl p-8 text-center space-y-4 border border-l-4 shadow-sm"
      style={{
        backgroundColor: 'var(--bg-card)',
        borderColor: 'var(--border-subtle)',
        borderLeftColor: 'var(--verdict-false-text)',
        color: 'var(--text-primary)',
      }}
    >
      <div
        className="inline-flex p-3 rounded-full border"
        style={{
          backgroundColor: 'var(--verdict-false-bg)',
          borderColor: 'var(--verdict-false-border)',
          color: 'var(--verdict-false-text)',
        }}
      >
        <AlertCircle className="w-6 h-6" />
      </div>
      <div className="space-y-1.5">
        <h3
          className="text-lg font-bold"
          style={{ fontFamily: 'var(--font-serif)', color: 'var(--verdict-false-text)' }}
        >
          Audit Service Network Error
        </h3>
        <p className="text-xs max-w-md mx-auto leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
          {message || 'Failed to communicate with ReelClaim backend service. Make sure the backend server is running.'}
        </p>
      </div>
      {onReset && (
        <button
          type="button"
          onClick={onReset}
          className="inline-flex items-center gap-2 px-4 py-2 rounded text-xs font-semibold border transition-all cursor-pointer hover:opacity-80"
          style={{
            backgroundColor: 'var(--bg-elevated)',
            borderColor: 'var(--border-med)',
            color: 'var(--text-primary)',
            fontFamily: 'var(--font-mono)',
          }}
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Retry Audit
        </button>
      )}
    </div>
  );
};
