import React from 'react';
import { CheckResponse } from '@/lib/types';
import { ShieldCheck, ShieldAlert, ShieldQuestion, Info, CheckCircle2, AlertTriangle, XCircle, HelpCircle } from 'lucide-react';

interface ReportHeaderProps {
  checkResult: CheckResponse;
  promotedSite: string | null;
}

export const ReportHeader: React.FC<ReportHeaderProps> = ({ checkResult, promotedSite }) => {
  const { trust_score, summary_label, score_breakdown, coverage_status } = checkResult;

  // Determine trust score badge styling if score is present
  const getScoreColor = (score: number) => {
    if (score >= 80) return 'from-emerald-500 to-teal-400 text-emerald-300 border-emerald-500/30 bg-emerald-950/40';
    if (score >= 40) return 'from-amber-500 to-yellow-400 text-amber-300 border-amber-500/30 bg-amber-950/40';
    return 'from-rose-500 to-red-400 text-rose-300 border-rose-500/30 bg-rose-950/40';
  };

  return (
    <div className="w-full bg-slate-900/80 border border-slate-800 rounded-2xl p-6 sm:p-8 backdrop-blur-xl shadow-2xl space-y-6">
      {/* Top Banner & Summary Label */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider px-2.5 py-1 rounded-full bg-indigo-950 text-indigo-400 border border-indigo-800/50">
              Cross-Check Audit Report
            </span>
            {promotedSite && (
              <span className="text-xs text-slate-400 truncate max-w-xs sm:max-w-md">
                Target: <code className="text-slate-200 bg-slate-800/80 px-2 py-0.5 rounded">{promotedSite}</code>
              </span>
            )}
          </div>
          {/* VERBATIM SUMMARY LABEL */}
          <h1 className="text-xl sm:text-2xl font-bold text-slate-100 tracking-tight">
            {summary_label}
          </h1>
        </div>

        {/* Score OR Neutral Unverified Badge */}
        <div className="flex-shrink-0">
          {trust_score !== null && trust_score !== undefined ? (
            <div className={`flex flex-col items-center justify-center p-4 rounded-xl border bg-gradient-to-br ${getScoreColor(trust_score)} min-w-[140px]`}>
              <span className="text-xs font-medium uppercase tracking-wider opacity-80">Trust Score</span>
              <div className="text-3xl font-extrabold tracking-tight mt-0.5">
                {trust_score}%
              </div>
            </div>
          ) : (
            /* NULL TRUST SCORE GUARDRAIL: Render neutral badge, NEVER 0% or score gauge */
            <div className="flex flex-col items-center justify-center p-4 rounded-xl border border-slate-700 bg-slate-800/60 text-slate-300 min-w-[170px]">
              <div className="flex items-center gap-1.5 text-slate-400 mb-1">
                <ShieldQuestion className="w-4 h-4 text-slate-400" />
                <span className="text-xs font-medium uppercase tracking-wider">Audit Status</span>
              </div>
              <div className="text-sm font-semibold text-slate-200 text-center">
                Unverified (No Data)
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Score Breakdown Pills */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="flex items-center gap-2.5 p-3 rounded-lg bg-emerald-950/20 border border-emerald-900/40">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
          <div>
            <div className="text-xs text-slate-400 font-medium">Confirmed</div>
            <div className="text-base font-bold text-emerald-300">{score_breakdown.confirmed_count}</div>
          </div>
        </div>

        <div className="flex items-center gap-2.5 p-3 rounded-lg bg-amber-950/20 border border-amber-900/40">
          <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0" />
          <div>
            <div className="text-xs text-slate-400 font-medium">Partial</div>
            <div className="text-base font-bold text-amber-300">{score_breakdown.partial_count}</div>
          </div>
        </div>

        <div className="flex items-center gap-2.5 p-3 rounded-lg bg-rose-950/20 border border-rose-900/40">
          <XCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
          <div>
            <div className="text-xs text-slate-400 font-medium">Contradicted</div>
            <div className="text-base font-bold text-rose-300">{score_breakdown.contradicted_count}</div>
          </div>
        </div>

        <div className="flex items-center gap-2.5 p-3 rounded-lg bg-slate-800/40 border border-slate-700/50">
          <HelpCircle className="w-4 h-4 text-slate-400 flex-shrink-0" />
          <div>
            <div className="text-xs text-slate-400 font-medium">Unaddressed</div>
            <div className="text-base font-bold text-slate-300">{score_breakdown.not_found_count}</div>
          </div>
        </div>
      </div>

      {/* Non-Negotiable Legal Disclaimer */}
      <div className="flex items-start gap-3 p-4 rounded-xl bg-amber-950/20 border border-amber-800/30 text-amber-200/90 text-sm leading-relaxed">
        <Info className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-amber-300">Important Disclaimer: </span>
          This checks the promoted site&apos;s own published claims — it does not verify the site&apos;s real-world legitimacy.
        </div>
      </div>
    </div>
  );
};
