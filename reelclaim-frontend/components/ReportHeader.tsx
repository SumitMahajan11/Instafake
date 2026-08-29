import React from 'react';
import { CheckResponse } from '@/lib/types';
import { Info, CheckCircle2, AlertTriangle, XCircle, HelpCircle, ExternalLink } from 'lucide-react';
import { TrustGauge } from './TrustGauge';

interface ReportHeaderProps {
  checkResult: CheckResponse;
  promotedSite: string | null;
}

export const ReportHeader: React.FC<ReportHeaderProps> = ({ checkResult, promotedSite }) => {
  const { trust_score, summary_label, score_breakdown } = checkResult;

  return (
    <div
      className="w-full p-5 space-y-5 border-b"
      style={{ borderColor: 'var(--border-subtle)' }}
    >
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        {/* Left: Target site info */}
        <div className="space-y-1 min-w-0 flex-1">
          <span
            className="text-[10px] uppercase tracking-widest"
            style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}
          >
            Audited Target
          </span>
          <div className="flex items-center gap-1.5 min-w-0">
            <ExternalLink className="w-3.5 h-3.5 flex-shrink-0" style={{ color: 'var(--text-muted)' }} />
            <span
              className="truncate text-sm font-semibold"
              style={{ color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}
            >
              {promotedSite || 'Site URL'}
            </span>
          </div>
          {summary_label && (
            <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>
              {summary_label}
            </p>
          )}
        </div>

        {/* Right: Trust Score Gauge */}
        <div
          className="border-l-0 sm:border-l sm:pl-5 pt-2 sm:pt-0 flex-shrink-0"
          style={{ borderColor: 'var(--border-subtle)' }}
        >
          <TrustGauge score={trust_score} label="Trust Score" />
        </div>
      </div>

      {/* Score Breakdown — flat stat row, no card wrapper */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="flex items-center gap-2">
          <span className="text-sm font-bold" style={{ fontFamily: 'var(--font-mono)', color: 'var(--verdict-verified-text)' }}>
            {score_breakdown?.confirmed_count ?? 0}
          </span>
          <div className="text-[10px] uppercase tracking-wider" style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
            Confirmed
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-sm font-bold" style={{ fontFamily: 'var(--font-mono)', color: 'var(--verdict-misleading-text)' }}>
            {score_breakdown?.partial_count ?? 0}
          </span>
          <div className="text-[10px] uppercase tracking-wider" style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
            Partial
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-sm font-bold" style={{ fontFamily: 'var(--font-mono)', color: 'var(--verdict-false-text)' }}>
            {score_breakdown?.contradicted_count ?? 0}
          </span>
          <div className="text-[10px] uppercase tracking-wider" style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
            Contradicted
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-sm font-bold" style={{ fontFamily: 'var(--font-mono)', color: 'var(--verdict-unverified-text)' }}>
            {score_breakdown?.not_found_count ?? 0}
          </span>
          <div className="text-[10px] uppercase tracking-wider" style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
            Unverified
          </div>
        </div>
      </div>

      {/* Disclaimer */}
      <div
        className="flex items-start gap-2 p-2.5 rounded border text-xs leading-relaxed"
        style={{
          backgroundColor: 'var(--bg-elevated)',
          borderColor: 'var(--border-subtle)',
          color: 'var(--text-secondary)',
        }}
      >
        <Info className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" style={{ color: 'var(--text-muted)' }} />
        <span>
          <strong style={{ color: 'var(--text-primary)' }}>Disclaimer:</strong>{' '}
          This checks the promoted site&apos;s published claims — it does not verify real-world legitimacy.
        </span>
      </div>
    </div>
  );
};
