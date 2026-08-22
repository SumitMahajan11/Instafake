'use client';

import React, { useState } from 'react';
import { AuditForm } from '@/components/AuditForm';
import { ReportHeader } from '@/components/ReportHeader';
import { CrawlStatusBanner } from '@/components/CrawlStatusBanner';
import { VerdictCard } from '@/components/VerdictCard';
import { EmptyState } from '@/components/EmptyState';
import { FullAuditResponse, ProgressStep } from '@/lib/types';
import { auditReel } from '@/lib/api';
import { ShieldCheck, RotateCcw } from 'lucide-react';

export default function Home() {
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [currentStep, setCurrentStep] = useState<ProgressStep>('idle');
  const [error, setError] = useState<string | null>(null);
  const [auditResult, setAuditResult] = useState<FullAuditResponse | null>(null);

  const handleAuditSubmit = async (caption: string, url: string) => {
    setIsLoading(true);
    setError(null);
    setAuditResult(null);
    setCurrentStep('extracting');

    try {
      const response = await auditReel(caption, url, (step) => {
        setCurrentStep(step);
      });
      setAuditResult(response);
      setCurrentStep('complete');
    } catch (err: any) {
      setError(err.message || 'Audit request failed');
      setCurrentStep('error');
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setAuditResult(null);
    setError(null);
    setCurrentStep('idle');
  };

  return (
    <main className="min-h-screen bg-[#090d16] text-slate-100 flex flex-col font-sans selection:bg-indigo-500 selection:text-white">
      {/* Top Navigation */}
      <header className="w-full border-b border-slate-800/80 bg-slate-950/60 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-indigo-600/20 border border-indigo-500/40 text-indigo-400">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <span className="text-lg font-black tracking-tight text-white flex items-center gap-1">
                Reel<span className="text-indigo-400">Claim</span>
              </span>
              <span className="text-[10px] block font-mono text-slate-500 uppercase tracking-widest">
                Truth & Verification Engine
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {auditResult && (
              <button
                type="button"
                onClick={handleReset}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300 border border-slate-700 transition-all cursor-pointer"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>New Audit</span>
              </button>
            )}
            <span className="text-xs font-mono font-medium px-2.5 py-1 rounded-full bg-slate-900 border border-slate-800 text-slate-400">
              v4.0 Phase 4
            </span>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <div className="flex-1 max-w-6xl mx-auto w-full px-4 sm:px-6 py-8 space-y-8">
        {/* Input Form */}
        <AuditForm
          onSubmit={handleAuditSubmit}
          isLoading={isLoading}
          currentStep={currentStep}
          error={error}
        />

        {/* Audit Results View */}
        {auditResult && (
          <div id="audit-report-container" className="space-y-6 animate-fadeIn">
            {/* Page Crawl Banner */}
            <CrawlStatusBanner
              crawlStatus={auditResult.crawl_status}
              promotedSite={auditResult.promoted_site}
            />

            {/* Zero Claims Extracted Edge State */}
            {auditResult.claims.length === 0 ? (
              <EmptyState type="zero_claims" onReset={handleReset} />
            ) : auditResult.check_result ? (
              <>
                {/* Header Block with Score / Unverified Badge & Disclaimer */}
                <ReportHeader
                  checkResult={auditResult.check_result}
                  promotedSite={auditResult.promoted_site}
                />

                {/* Verdict Cards List */}
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-bold text-slate-100 tracking-tight">
                      Evaluated Claims & Site Evidence ({auditResult.check_result.verdicts.length})
                    </h3>
                    <span className="text-xs text-slate-400 font-mono">
                      Pass 1 (Aliases) + Pass 2 (LLM) + Pass 3 (Guardrail)
                    </span>
                  </div>

                  <div className="space-y-4">
                    {auditResult.check_result.verdicts.map((item, idx) => (
                      <VerdictCard key={idx} verdictItem={item} index={idx} />
                    ))}
                  </div>
                </div>
              </>
            ) : auditResult.crawl_status === 'blocked' || auditResult.crawl_status === 'failed' ? (
              <EmptyState type="blocked_site" onReset={handleReset} />
            ) : null}
          </div>
        )}

        {/* Network / Connection Error State */}
        {currentStep === 'error' && !auditResult && (
          <EmptyState
            type="network_error"
            message={error || undefined}
            onReset={handleReset}
          />
        )}
      </div>

      {/* Footer */}
      <footer className="w-full border-t border-slate-800/80 bg-slate-950/40 py-6 text-center text-xs text-slate-500">
        <p>ReelClaim — Stateless Claim Verification Engine. All site facts crawled in real time.</p>
      </footer>
    </main>
  );
}
