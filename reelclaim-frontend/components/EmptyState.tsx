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
      <div className="w-full bg-slate-900/80 border border-slate-800 rounded-2xl p-8 text-center space-y-4 shadow-xl">
        <div className="inline-flex p-3 rounded-full bg-slate-800 text-slate-400">
          <FileQuestion className="w-8 h-8" />
        </div>
        <div className="space-y-1">
          <h3 className="text-xl font-bold text-slate-100">No Verifiable Claims Extracted</h3>
          <p className="text-sm text-slate-400 max-w-md mx-auto">
            The provided social caption did not contain explicit promotional claims (such as pricing, refunds, eligibility, or certificates).
          </p>
        </div>
        {onReset && (
          <button
            type="button"
            onClick={onReset}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-semibold transition-all cursor-pointer"
          >
            <RefreshCw className="w-4 h-4" />
            Try Another Caption
          </button>
        )}
      </div>
    );
  }

  if (type === 'blocked_site') {
    return (
      <div className="w-full bg-amber-950/30 border border-amber-800/60 rounded-2xl p-8 text-center space-y-4 shadow-xl text-amber-200">
        <div className="inline-flex p-3 rounded-full bg-amber-950 text-amber-400 border border-amber-800/80">
          <ShieldAlert className="w-8 h-8" />
        </div>
        <div className="space-y-1">
          <h3 className="text-xl font-bold text-amber-300">Could Not Verify Site — Proceed With Caution</h3>
          <p className="text-sm text-amber-200/80 max-w-lg mx-auto">
            {message || 'The target website blocked automated access (e.g. Cloudflare bot challenge or anti-scraping wall). Claims could not be cross-checked against published site pages.'}
          </p>
        </div>
        {onReset && (
          <button
            type="button"
            onClick={onReset}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-amber-900/60 hover:bg-amber-800/60 text-amber-100 text-sm font-semibold transition-all cursor-pointer"
          >
            <RefreshCw className="w-4 h-4" />
            Audit Different URL
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="w-full bg-rose-950/30 border border-rose-900/60 rounded-2xl p-8 text-center space-y-4 shadow-xl text-rose-200">
      <div className="inline-flex p-3 rounded-full bg-rose-950 text-rose-400 border border-rose-800/80">
        <AlertCircle className="w-8 h-8" />
      </div>
      <div className="space-y-1">
        <h3 className="text-xl font-bold text-rose-300">Audit Service Network Error</h3>
        <p className="text-sm text-rose-200/80 max-w-md mx-auto">
          {message || 'Failed to communicate with ReelClaim backend service. Make sure the backend server is running.'}
        </p>
      </div>
      {onReset && (
        <button
          type="button"
          onClick={onReset}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-rose-900/60 hover:bg-rose-800/60 text-rose-100 text-sm font-semibold transition-all cursor-pointer"
        >
          <RefreshCw className="w-4 h-4" />
          Retry Audit
        </button>
      )}
    </div>
  );
};
