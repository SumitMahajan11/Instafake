'use client';

import React, { useState } from 'react';
import { Copy, Check, Share2, Link as LinkIcon } from 'lucide-react';

interface CaseIdBannerProps {
  auditId: string;
}

export function CaseIdBanner({ auditId }: CaseIdBannerProps) {
  const [copied, setCopied] = useState<boolean>(false);

  const shareableUrl = typeof window !== 'undefined'
    ? `${window.location.origin}?audit=${auditId}`
    : `?audit=${auditId}`;

  const handleCopyLink = async () => {
    try {
      await navigator.clipboard.writeText(shareableUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy share URL', err);
    }
  };

  return (
    <div
      className="p-3 rounded-md border flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs"
      style={{
        backgroundColor: 'var(--bg-card)',
        borderColor: 'var(--border-subtle)',
      }}
    >
      <div className="flex items-center gap-2 min-w-0">
        <Share2 className="w-4 h-4 flex-shrink-0" style={{ color: 'var(--text-muted)' }} />
        <div className="min-w-0">
          <span className="font-mono text-[10px] uppercase tracking-wider block" style={{ color: 'var(--text-muted)' }}>
            Case ID Ledger Record
          </span>
          <span className="font-mono font-bold text-xs truncate block" style={{ color: 'var(--text-primary)' }}>
            {auditId}
          </span>
        </div>
      </div>

      <button
        type="button"
        onClick={handleCopyLink}
        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded font-mono text-xs font-semibold border cursor-pointer hover:opacity-80 transition-all self-start sm:self-auto flex-shrink-0"
        style={{
          backgroundColor: copied ? 'var(--verdict-verified-bg)' : 'var(--bg-elevated)',
          borderColor: copied ? 'var(--verdict-verified-border)' : 'var(--border-subtle)',
          color: copied ? 'var(--verdict-verified-text)' : 'var(--text-primary)',
        }}
      >
        {copied ? (
          <>
            <Check className="w-3.5 h-3.5" />
            <span>Copied Link!</span>
          </>
        ) : (
          <>
            <LinkIcon className="w-3.5 h-3.5" />
            <span>Copy Share Link</span>
          </>
        )}
      </button>
    </div>
  );
}
