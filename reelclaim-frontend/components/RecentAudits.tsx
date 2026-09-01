'use client';

import React, { useEffect, useState } from 'react';
import { fetchRecentAudits } from '@/lib/api';
import { RecentAuditItem } from '@/lib/types';
import { History, RefreshCw, ChevronRight, Database, ExternalLink } from 'lucide-react';

interface RecentAuditsProps {
  onSelectAudit: (auditId: string) => void;
  selectedAuditId?: string;
  refreshTrigger?: number;
}

export function RecentAudits({ onSelectAudit, selectedAuditId, refreshTrigger }: RecentAuditsProps) {
  const [audits, setAudits] = useState<RecentAuditItem[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [persistenceDisabled, setPersistenceDisabled] = useState<boolean>(false);

  const loadAudits = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchRecentAudits(10, 0);
      setAudits(data.audits || []);
      setTotal(data.total || 0);
      if (data.persistence === 'disabled') {
        setPersistenceDisabled(true);
      } else {
        setPersistenceDisabled(false);
      }
    } catch (err: any) {
      setError('Failed to load recent audits.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadAudits();
  }, [refreshTrigger]);

  if (persistenceDisabled) {
    return (
      <div className="mt-6 pt-4 border-t" style={{ borderColor: 'var(--border-subtle)' }}>
        <div className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider mb-2" style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
          <Database className="w-3.5 h-3.5" />
          <span>Recent Audits</span>
        </div>
        <p className="text-xs italic" style={{ color: 'var(--text-muted)' }}>
          Database persistence is disabled in current environment (DATABASE_URL unset).
        </p>
      </div>
    );
  }

  return (
    <div className="mt-6 pt-4 border-t" style={{ borderColor: 'var(--border-subtle)' }}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider" style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
          <History className="w-3.5 h-3.5" />
          <span>Recent Audits ({total})</span>
        </div>
        <button
          type="button"
          onClick={loadAudits}
          disabled={isLoading}
          className="p-1 rounded hover:opacity-80 transition-opacity"
          title="Refresh list"
          style={{ color: 'var(--text-muted)' }}
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {error ? (
        <p className="text-xs" style={{ color: 'var(--verdict-contradicted-text)' }}>{error}</p>
      ) : audits.length === 0 ? (
        <p className="text-xs italic" style={{ color: 'var(--text-muted)' }}>No persisted audits yet.</p>
      ) : (
        <div className="space-y-2 max-h-[280px] overflow-y-auto pr-1">
          {audits.map((item) => {
            const isSelected = selectedAuditId === item.id;
            const createdDate = item.created_at ? new Date(item.created_at).toLocaleDateString() : '';

            return (
              <button
                key={item.id}
                type="button"
                onClick={() => onSelectAudit(item.id)}
                className={`w-full text-left p-2.5 rounded border text-xs transition-all flex items-start justify-between gap-2 group ${
                  isSelected ? 'border-primary' : 'hover:border-bright'
                }`}
                style={{
                  backgroundColor: isSelected ? 'var(--bg-elevated)' : 'var(--bg-card)',
                  borderColor: isSelected ? 'var(--border-bright)' : 'var(--border-subtle)',
                }}
              >
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span
                      className="font-mono text-[10px] px-1.5 py-0.5 rounded border"
                      style={{
                        backgroundColor: 'var(--bg)',
                        borderColor: 'var(--border-subtle)',
                        color: 'var(--text-secondary)',
                      }}
                    >
                      {item.id.substring(0, 8)}
                    </span>
                    {item.trust_score !== null && item.trust_score !== undefined ? (
                      <span
                        className="font-mono text-[10px] font-bold px-1.5 py-0.5 rounded"
                        style={{
                          backgroundColor: item.trust_score >= 80 ? 'var(--verdict-verified-bg)' : item.trust_score >= 50 ? 'var(--verdict-partial-bg)' : 'var(--verdict-contradicted-bg)',
                          color: item.trust_score >= 80 ? 'var(--verdict-verified-text)' : item.trust_score >= 50 ? 'var(--verdict-partial-text)' : 'var(--verdict-contradicted-text)',
                        }}
                      >
                        {Math.round(item.trust_score)}% Trust
                      </span>
                    ) : (
                      <span className="font-mono text-[10px] px-1.5 py-0.5 rounded" style={{ backgroundColor: 'var(--bg-elevated)', color: 'var(--text-muted)' }}>
                        Unverified
                      </span>
                    )}
                  </div>
                  <p className="line-clamp-2 leading-relaxed" style={{ color: 'var(--text-primary)' }}>
                    {item.caption}
                  </p>
                  {createdDate && (
                    <span className="text-[10px] mt-1 block" style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                      {createdDate}
                    </span>
                  )}
                </div>
                <ChevronRight className="w-4 h-4 flex-shrink-0 mt-1 opacity-40 group-hover:opacity-100 transition-opacity" style={{ color: 'var(--text-muted)' }} />
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
