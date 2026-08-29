import React from 'react';
import { RefreshCw, AlertTriangle } from 'lucide-react';
import { CrawlStatus } from '@/lib/types';

interface CrawlStatusBannerProps {
  crawlStatus: CrawlStatus | string | null;
  promotedSite: string | null;
  onRetry?: () => void;
}

export const CrawlStatusBanner: React.FC<CrawlStatusBannerProps> = ({ crawlStatus, promotedSite, onRetry }) => {
  // Map "success" or null/empty to return nothing at all
  if (!crawlStatus || crawlStatus === 'success') {
    return null;
  }

  // OVERLOADED STATE: server memory capacity ceiling (psutil circuit breaker), static alert, manual retry framing
  if (crawlStatus === 'overloaded') {
    return (
      <div
        className="w-full rounded-xl border-l-4 p-4 shadow-sm space-y-2 border transition-all"
        style={{
          backgroundColor: 'var(--bg-card)',
          borderColor: 'var(--border-subtle)',
          borderLeftColor: 'var(--verdict-false-text)',
        }}
      >
        <div className="flex items-center gap-2 font-bold text-xs" style={{ color: 'var(--verdict-false-text)' }}>
          <AlertTriangle className="w-4 h-4 flex-shrink-0" style={{ color: 'var(--verdict-false-text)' }} />
          <span>Server at Capacity</span>
        </div>
        <p className="text-xs leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
          The verification server is currently operating at maximum memory capacity. Please wait ~20s and try again.
        </p>
        {onRetry && (
          <div className="pt-1">
            <button
              type="button"
              onClick={onRetry}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all cursor-pointer hover:opacity-80"
              style={{
                backgroundColor: 'var(--bg-elevated)',
                borderColor: 'var(--border-med)',
                color: 'var(--text-primary)',
                fontFamily: 'var(--font-mono)',
              }}
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Try Again (Manual)</span>
            </button>
          </div>
        )}
      </div>
    );
  }

  // BUSY STATE: warn style, pulsing dot, retry-attempt copy
  if (crawlStatus === 'busy') {
    return (
      <div
        className="w-full rounded-xl border-l-4 p-4 shadow-sm space-y-2 border transition-all"
        style={{
          backgroundColor: 'var(--bg-card)',
          borderColor: 'var(--border-subtle)',
          borderLeftColor: 'var(--verdict-misleading-text)',
        }}
      >
        <div className="flex items-center gap-2 font-bold text-xs" style={{ color: 'var(--verdict-misleading-text)' }}>
          <span className="w-2 h-2 rounded-full animate-ping inline-block" style={{ backgroundColor: 'var(--verdict-misleading-text)' }} />
          <span>Server Capacity Busy</span>
        </div>
        <p className="text-xs leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
          Server is currently busy handling high traffic. Please wait a few moments and try your audit again.
        </p>
        {onRetry && (
          <div className="pt-1">
            <button
              type="button"
              onClick={onRetry}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all cursor-pointer hover:opacity-80"
              style={{
                backgroundColor: 'var(--bg-elevated)',
                borderColor: 'var(--border-med)',
                color: 'var(--text-primary)',
              }}
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Try Again</span>
            </button>
          </div>
        )}
      </div>
    );
  }

  // DEGRADED STATE: warn style, inline notice with static/subtle dot
  if (crawlStatus === 'degraded') {
    return (
      <div
        className="w-full rounded-xl border-l-4 p-3.5 shadow-sm flex items-center justify-between gap-3 text-xs border"
        style={{
          backgroundColor: 'var(--bg-card)',
          borderColor: 'var(--border-subtle)',
          borderLeftColor: 'var(--verdict-misleading-text)',
          color: 'var(--text-secondary)',
        }}
      >
        <div className="flex items-center gap-2 min-w-0">
          <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: 'var(--verdict-misleading-text)' }} />
          <span className="truncate">
            <strong style={{ color: 'var(--text-primary)' }}>Partial page data extracted</strong> — JS hydration timeout on{' '}
            <code className="px-1.5 py-0.5 rounded font-mono text-[11px]" style={{ backgroundColor: 'var(--bg-elevated)', color: 'var(--text-primary)' }}>
              {promotedSite || 'target domain'}
            </code>.
          </span>
        </div>
        <span
          className="px-2 py-0.5 rounded-full border text-[10px] font-bold uppercase tracking-wider flex-shrink-0"
          style={{
            backgroundColor: 'var(--verdict-misleading-bg)',
            borderColor: 'var(--verdict-misleading-border)',
            color: 'var(--verdict-misleading-text)',
          }}
        >
          Degraded
        </span>
      </div>
    );
  }

  // BLOCKED STATE: danger style, static dot, NO retry button
  if (crawlStatus === 'blocked') {
    return (
      <div
        className="w-full rounded-xl border-l-4 p-4 shadow-sm space-y-1.5 border transition-all"
        style={{
          backgroundColor: 'var(--bg-card)',
          borderColor: 'var(--border-subtle)',
          borderLeftColor: 'var(--verdict-false-text)',
        }}
      >
        <div className="flex items-center gap-2 font-bold text-xs" style={{ color: 'var(--verdict-false-text)' }}>
          <span className="w-2 h-2 rounded-full inline-block" style={{ backgroundColor: 'var(--verdict-false-text)' }} />
          <span>Site Blocked Verification Crawler</span>
        </div>
        <p className="text-xs leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
          The promoted website <code className="px-1.5 py-0.5 rounded font-mono text-[11px]" style={{ backgroundColor: 'var(--bg-elevated)', color: 'var(--text-primary)' }}>{promotedSite || 'target domain'}</code> returned an anti-bot challenge (WAF / Cloudflare wall). Automated cross-checking cannot read this site.
        </p>
      </div>
    );
  }

  // FAILED STATE: danger style, static dot, WITH manual retry button
  if (crawlStatus === 'failed') {
    return (
      <div
        className="w-full rounded-xl border-l-4 p-4 shadow-sm space-y-2 border transition-all"
        style={{
          backgroundColor: 'var(--bg-card)',
          borderColor: 'var(--border-subtle)',
          borderLeftColor: 'var(--verdict-false-text)',
        }}
      >
        <div className="flex items-center gap-2 font-bold text-xs" style={{ color: 'var(--verdict-false-text)' }}>
          <span className="w-2 h-2 rounded-full inline-block" style={{ backgroundColor: 'var(--verdict-false-text)' }} />
          <span>Couldn't Reach or Read Target Site</span>
        </div>
        <p className="text-xs leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
          The promoted website <code className="px-1.5 py-0.5 rounded font-mono text-[11px]" style={{ backgroundColor: 'var(--bg-elevated)', color: 'var(--text-primary)' }}>{promotedSite || 'target domain'}</code> failed to respond or returned an unreadable response.
        </p>
        {onRetry && (
          <div className="pt-1">
            <button
              type="button"
              onClick={onRetry}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all cursor-pointer hover:opacity-80"
              style={{
                backgroundColor: 'var(--bg-elevated)',
                borderColor: 'var(--border-med)',
                color: 'var(--text-primary)',
              }}
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Try Again</span>
            </button>
          </div>
        )}
      </div>
    );
  }

  // NO_URL_FOUND STATE: subtle warn notice card
  if (crawlStatus === 'no_url_found') {
    return (
      <div
        className="w-full rounded-xl border-l-4 p-3.5 shadow-sm space-y-1 border text-xs"
        style={{
          backgroundColor: 'var(--bg-card)',
          borderColor: 'var(--border-subtle)',
          borderLeftColor: 'var(--verdict-unverified-text)',
        }}
      >
        <div className="flex items-center gap-2 font-bold text-xs" style={{ color: 'var(--text-primary)' }}>
          <span className="w-2 h-2 rounded-full inline-block" style={{ backgroundColor: 'var(--verdict-unverified-text)' }} />
          <span>No Site URL Provided</span>
        </div>
        <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>
          The caption did not contain a valid URL and no override URL was submitted. Claims were extracted but cross-checking requires a site URL.
        </p>
      </div>
    );
  }

  return null;
};
