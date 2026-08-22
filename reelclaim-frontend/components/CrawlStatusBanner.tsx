import React from 'react';
import { Globe, AlertTriangle, ShieldAlert, CheckCircle } from 'lucide-react';

interface CrawlStatusBannerProps {
  crawlStatus: string | null;
  promotedSite: string | null;
}

export const CrawlStatusBanner: React.FC<CrawlStatusBannerProps> = ({ crawlStatus, promotedSite }) => {
  if (!crawlStatus) return null;

  if (crawlStatus === 'blocked' || crawlStatus === 'failed') {
    return (
      <div className="w-full bg-amber-950/40 border border-amber-800/60 rounded-xl p-5 shadow-lg space-y-2 text-amber-200">
        <div className="flex items-center gap-2.5 font-bold text-amber-300 text-base">
          <ShieldAlert className="w-5 h-5 text-amber-400 flex-shrink-0" />
          <span>Could Not Verify Site — Proceed With Caution</span>
        </div>
        <p className="text-sm text-amber-200/80 leading-relaxed">
          The promoted website <code className="bg-amber-900/60 px-1.5 py-0.5 rounded text-amber-100 font-mono text-xs">{promotedSite || 'target domain'}</code> blocked automated verification or failed to respond (e.g. Cloudflare bot challenge or anti-scraping wall).
        </p>
      </div>
    );
  }

  if (crawlStatus === 'no_url_found') {
    return (
      <div className="w-full bg-slate-900/60 border border-slate-800 rounded-xl p-5 text-slate-300 space-y-1">
        <div className="flex items-center gap-2 font-semibold text-slate-200">
          <Globe className="w-4 h-4 text-slate-400" />
          <span>No Promoted Site URL Provided or Extracted</span>
        </div>
        <p className="text-xs text-slate-400">
          The caption did not contain a valid URL and no override URL was submitted. Claims were extracted but cross-checking requires a site URL.
        </p>
      </div>
    );
  }

  return (
    <div className="w-full bg-slate-900/60 border border-slate-800/80 rounded-xl p-4 flex items-center justify-between gap-4 text-xs text-slate-300">
      <div className="flex items-center gap-2">
        <CheckCircle className="w-4 h-4 text-emerald-400 flex-shrink-0" />
        <span>
          Website crawl completed successfully for <code className="text-indigo-300 font-mono bg-slate-800 px-1.5 py-0.5 rounded">{promotedSite}</code>
        </span>
      </div>
      <div className="flex items-center gap-1.5">
        <span className="px-2 py-0.5 rounded-full bg-emerald-950 text-emerald-400 border border-emerald-800/60 font-semibold uppercase text-[10px]">
          Pages Audited
        </span>
      </div>
    </div>
  );
};
