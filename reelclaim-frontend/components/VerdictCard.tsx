import React, { useState } from 'react';
import { ClaimVerdict } from '@/lib/types';
import { ExternalLink, ChevronDown, ChevronUp } from 'lucide-react';

interface VerdictCardProps {
  verdictItem: ClaimVerdict;
  index: number;
}

export const VerdictCard: React.FC<VerdictCardProps> = ({ verdictItem, index }) => {
  const [showReasoning, setShowReasoning] = useState<boolean>(false);

  const { claim_text, verdict, evidence_text, source_url, reasoning } = verdictItem;

  // Format index as 01, 02, 03... using IBM Plex Mono
  const formattedIndex = String(index + 1).padStart(2, '0');

  // Helper to extract domain name cleanly from source_url
  const getDomainName = (url: string | null): string => {
    if (!url) return 'target domain';
    try {
      const parsed = new URL(url);
      return parsed.hostname.replace(/^www\./, '');
    } catch {
      return url;
    }
  };

  // Map API verdict to display label, colors, border accent, and stamp rotation angle
  const getVerdictDetails = () => {
    switch (verdict) {
      case 'confirmed':
        return {
          label: 'VERIFIED',
          stampColor: 'var(--verdict-verified-text)',
          stampBorder: 'var(--verdict-verified-border)',
          stampBg: 'var(--verdict-verified-bg)',
          leftAccentBorder: 'var(--verdict-verified-text)',
          rotateAngle: '-4deg',
        };
      case 'contradicted':
        return {
          label: 'CONTRADICTED',
          stampColor: 'var(--verdict-false-text)',
          stampBorder: 'var(--verdict-false-border)',
          stampBg: 'var(--verdict-false-bg)',
          leftAccentBorder: 'var(--verdict-false-text)',
          rotateAngle: '6deg',
        };
      case 'partial':
        return {
          label: 'PARTIAL',
          stampColor: 'var(--verdict-misleading-text)',
          stampBorder: 'var(--verdict-misleading-border)',
          stampBg: 'var(--verdict-misleading-bg)',
          leftAccentBorder: 'var(--verdict-misleading-text)',
          rotateAngle: '-3deg',
        };
      case 'not_found':
      default:
        return {
          label: 'UNVERIFIED',
          stampColor: 'var(--verdict-unverified-text)',
          stampBorder: 'var(--verdict-unverified-border)',
          stampBg: 'var(--verdict-unverified-bg)',
          leftAccentBorder: 'var(--border-bright)',
          rotateAngle: '5deg',
        };
    }
  };

  const details = getVerdictDetails();
  const domainName = getDomainName(source_url);

  return (
    <div
      className="w-full rounded-xl border p-4.5 sm:p-5 transition-all space-y-3 shadow-sm relative overflow-hidden"
      style={{
        backgroundColor: 'var(--bg-card)',
        borderColor: 'var(--border-subtle)',
        boxShadow: 'var(--shadow-card)',
      }}
    >
      {/* Top Main Section: Flex layout with entry content on left & stamp badge on right */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        
        {/* Left Column: Numbered Entry + Claim Content + Left Accent Border */}
        <div className="flex items-start gap-3.5 flex-1 min-w-0">
          {/* Entry Number (01, 02, ...) in IBM Plex Mono */}
          <span
            className="text-xs sm:text-sm font-bold tracking-wider pt-0.5 select-none flex-shrink-0"
            style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}
          >
            {formattedIndex}
          </span>

          {/* Claim Text and Evidence block with left border accent */}
          <div
            className="border-l-2 pl-3.5 space-y-1.5 flex-1 min-w-0"
            style={{ borderColor: details.leftAccentBorder }}
          >
            {/* Main Claim Text */}
            <p className="text-sm font-medium leading-relaxed" style={{ color: 'var(--text-primary)' }}>
              {claim_text}
            </p>

            {/* Short Evidence Line + Source Link */}
            <div className="flex flex-wrap items-center gap-1.5 text-xs" style={{ color: 'var(--text-secondary)' }}>
              {evidence_text ? (
                <span>
                  &ldquo;{evidence_text}&rdquo; —{' '}
                  <span className="font-semibold" style={{ color: 'var(--text-primary)' }}>
                    {domainName}
                  </span>
                </span>
              ) : (
                <span className="italic text-[11px]" style={{ color: 'var(--text-muted)' }}>
                  No matching claim found on {domainName}
                </span>
              )}

              {source_url && (
                <a
                  href={source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-[11px] font-medium hover:underline ml-1"
                  style={{ color: 'var(--text-accent)' }}
                >
                  <span>Link</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
              )}
            </div>
          </div>
        </div>

        {/* Right Column: Rotated Stamp Badge with "thud" Animation */}
        {/* On mobile (<640px), stamp positions inline under the text */}
        <div className="self-end sm:self-center flex-shrink-0 pt-1 sm:pt-0">
          <div
            className="animate-stamp-thud inline-block px-3 py-1.5 rounded border-2 text-xs font-black tracking-widest uppercase shadow-sm select-none"
            style={{
              fontFamily: 'var(--font-mono)',
              color: details.stampColor,
              borderColor: details.stampBorder,
              backgroundColor: details.stampBg,
              ['--stamp-angle' as any]: details.rotateAngle,
              transform: `rotate(${details.rotateAngle})`,
            }}
          >
            {details.label}
          </div>
        </div>

      </div>

      {/* "Why?" Reasoning Toggle */}
      <div className="pt-1 border-t" style={{ borderColor: 'var(--border-subtle)' }}>
        <button
          type="button"
          onClick={() => setShowReasoning(!showReasoning)}
          className="inline-flex items-center gap-1 text-xs transition-colors cursor-pointer font-medium hover:opacity-80"
          style={{ color: 'var(--text-muted)' }}
        >
          <span>Why this verdict?</span>
          {showReasoning ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </button>

        {showReasoning && (
          <div
            className="mt-2 p-3 rounded-lg border text-xs leading-relaxed animate-fadeIn"
            style={{
              backgroundColor: 'var(--bg-elevated)',
              borderColor: 'var(--border-subtle)',
              color: 'var(--text-secondary)',
            }}
          >
            <span className="font-semibold" style={{ color: 'var(--text-secondary)' }}>Reasoning: </span>
            {reasoning}
          </div>
        )}
      </div>
    </div>
  );
};
