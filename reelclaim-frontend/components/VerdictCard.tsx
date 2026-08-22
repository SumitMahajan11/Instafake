import React, { useState } from 'react';
import { ClaimVerdict } from '@/lib/types';
import { ExternalLink, CheckCircle2, XCircle, AlertTriangle, HelpCircle, ChevronDown, ChevronUp, Tag } from 'lucide-react';

interface VerdictCardProps {
  verdictItem: ClaimVerdict;
  index: number;
}

export const VerdictCard: React.FC<VerdictCardProps> = ({ verdictItem, index }) => {
  const [showReasoning, setShowReasoning] = useState<boolean>(false);

  const { claim_text, category, source_type, verdict, evidence_text, source_url, reasoning } = verdictItem;

  // Verdict badge configuration & visual hierarchy styles
  const getVerdictStyle = () => {
    switch (verdict) {
      case 'confirmed':
        return {
          containerStyle: 'bg-emerald-950/20 border-emerald-900/40 hover:border-emerald-800/60 shadow-emerald-950/10',
          badgeBg: 'bg-emerald-950/80 text-emerald-300 border-emerald-700/60',
          icon: <CheckCircle2 className="w-4 h-4 text-emerald-400" />,
          label: 'Confirmed',
          headerGlow: 'text-emerald-300'
        };
      case 'contradicted':
        return {
          containerStyle: 'bg-rose-950/30 border-rose-900/60 hover:border-rose-700/80 shadow-lg shadow-rose-950/30 ring-1 ring-rose-900/40',
          badgeBg: 'bg-rose-950 text-rose-300 border-rose-700/80 font-bold',
          icon: <XCircle className="w-4 h-4 text-rose-400" />,
          label: 'Contradicted',
          headerGlow: 'text-rose-300'
        };
      case 'partial':
        return {
          containerStyle: 'bg-amber-950/20 border-amber-900/40 hover:border-amber-800/60 shadow-amber-950/10',
          badgeBg: 'bg-amber-950/80 text-amber-300 border-amber-700/60',
          icon: <AlertTriangle className="w-4 h-4 text-amber-400" />,
          label: 'Partial',
          headerGlow: 'text-amber-300'
        };
      case 'not_found':
      default:
        return {
          // Visual hierarchy rule: not_found rows recede relative to contradicted rows
          containerStyle: 'bg-slate-900/40 border-slate-800/40 hover:border-slate-700/60 opacity-80',
          badgeBg: 'bg-slate-800/80 text-slate-400 border-slate-700/50',
          icon: <HelpCircle className="w-4 h-4 text-slate-400" />,
          label: 'Not Found on Site',
          headerGlow: 'text-slate-400'
        };
    }
  };

  const style = getVerdictStyle();

  return (
    <div className={`w-full rounded-xl border p-5 transition-all space-y-4 ${style.containerStyle}`}>
      {/* Top Bar: Claim Index, Category Badge, Verdict Badge */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800/60 pb-3">
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono font-bold text-slate-400 px-2 py-0.5 bg-slate-800 rounded">
            #{index + 1}
          </span>
          <span className="inline-flex items-center gap-1 text-xs font-medium text-slate-300 px-2.5 py-0.5 rounded-full bg-slate-800/80 border border-slate-700/50 capitalize">
            <Tag className="w-3 h-3 text-indigo-400" />
            {category}
          </span>
          <span className="text-[11px] font-mono text-slate-500 uppercase tracking-wider">
            [{source_type}]
          </span>
        </div>

        {/* Verdict Badge */}
        <div className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold border ${style.badgeBg}`}>
          {style.icon}
          <span>{style.label}</span>
        </div>
      </div>

      {/* Side-by-Side "Reel Says" vs "Site Says" Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
        {/* Left Column: Reel Says */}
        <div className="space-y-1.5 p-3.5 rounded-lg bg-slate-950/60 border border-slate-800/60">
          <div className="text-xs font-bold uppercase tracking-wider text-slate-400">
            Reel Claimed
          </div>
          <p className="text-slate-200 font-medium leading-relaxed">
            &ldquo;{claim_text}&rdquo;
          </p>
        </div>

        {/* Right Column: Site Says */}
        <div className="space-y-1.5 p-3.5 rounded-lg bg-slate-950/60 border border-slate-800/60 flex flex-col justify-between">
          <div>
            <div className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Site Evidence
            </div>
            {evidence_text ? (
              <blockquote className="text-slate-200 italic leading-relaxed mt-1 border-l-2 border-indigo-500 pl-3">
                &ldquo;{evidence_text}&rdquo;
              </blockquote>
            ) : (
              <p className="text-slate-400 italic mt-1 text-xs">
                Not addressed on the site
              </p>
            )}
          </div>

          {/* Source Link */}
          {source_url && (
            <div className="pt-2">
              <a
                href={source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 text-xs text-indigo-400 hover:text-indigo-300 hover:underline font-medium"
              >
                <span>View Source Page</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
            </div>
          )}
        </div>
      </div>

      {/* "Why?" Reasoning Toggle */}
      <div className="pt-1">
        <button
          type="button"
          onClick={() => setShowReasoning(!showReasoning)}
          className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 transition-colors cursor-pointer font-medium"
        >
          <span>Why this verdict?</span>
          {showReasoning ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </button>

        {showReasoning && (
          <div className="mt-2.5 p-3 rounded-lg bg-slate-950/80 border border-slate-800 text-xs text-slate-300 leading-relaxed animate-fadeIn">
            <span className="font-semibold text-indigo-400">Reasoning: </span>
            {reasoning}
          </div>
        )}
      </div>
    </div>
  );
};
