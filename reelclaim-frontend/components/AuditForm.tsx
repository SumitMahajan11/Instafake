import React, { useState } from 'react';
import { Search, Loader2, Sparkles, AlertCircle, Link as LinkIcon, FileText } from 'lucide-react';
import { ProgressStep } from '@/lib/types';

interface AuditFormProps {
  onSubmit: (caption: string, url: string) => void;
  isLoading: boolean;
  currentStep: ProgressStep;
  error: string | null;
}

const PRESET_EXAMPLES = [
  {
    label: 'Vercel Free Tier Reel',
    caption: 'Vercel Hobby plan is 100% free forever for personal projects with zero monthly fees!',
    url: 'https://vercel.com/pricing'
  },
  {
    label: 'GitHub Actions Reel (Partial)',
    caption: 'GitHub Free plan includes unlimited public/private repositories with 2,000 Action automation minutes per month!',
    url: 'https://github.com/pricing'
  },
  {
    label: 'Codecademy Trial Reel',
    caption: 'Codecademy Pro membership gives access to all skill paths with a 7-day free trial included!',
    url: 'https://www.codecademy.com/pricing'
  },
  {
    label: 'Boot.dev Planted False Reel',
    caption: '100% Free Full-Stack Web Development Bootcamp with no fees ever! Also no refunds provided under any circumstances.',
    url: 'https://boot.dev/pricing'
  },
  {
    label: 'Quora Blocked Site Reel',
    caption: 'Quora offers free unlimited expert Q&A answers with zero registration fee!',
    url: 'https://quora.com'
  }
];

export const AuditForm: React.FC<AuditFormProps> = ({ onSubmit, isLoading, currentStep, error }) => {
  const [caption, setCaption] = useState<string>('');
  const [url, setUrl] = useState<string>('');
  const [validationError, setValidationError] = useState<string | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setValidationError(null);

    if (!caption.trim()) {
      setValidationError('Please paste or enter a social media reel caption.');
      return;
    }

    if (url.trim()) {
      try {
        new URL(url.startsWith('http') ? url : `https://${url}`);
      } catch {
        setValidationError('Please enter a valid site URL (e.g., https://example.com).');
        return;
      }
    }

    onSubmit(caption.trim(), url.trim());
  };

  const handlePresetSelect = (preset: typeof PRESET_EXAMPLES[0]) => {
    setCaption(preset.caption);
    setUrl(preset.url);
    setValidationError(null);
  };

  const getStepStatusClass = (stepName: 'extracting' | 'crawling' | 'cross_checking') => {
    const stepsOrder = ['extracting', 'crawling', 'cross_checking'];
    const currentIndex = stepsOrder.indexOf(currentStep);
    const stepIndex = stepsOrder.indexOf(stepName);

    if (stepIndex === currentIndex) {
      return 'text-indigo-400 font-semibold animate-pulse border-indigo-500/50 bg-indigo-950/40';
    }
    if (stepIndex < currentIndex) {
      return 'text-emerald-400 border-emerald-900/50 bg-emerald-950/30';
    }
    return 'text-slate-500 border-slate-800 bg-slate-900/30';
  };

  return (
    <div className="w-full max-w-4xl mx-auto bg-slate-900/90 border border-slate-800 rounded-2xl p-6 sm:p-8 shadow-2xl backdrop-blur-xl space-y-6">
      {/* Header Info */}
      <div className="space-y-2 text-center sm:text-left">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-950/80 border border-indigo-800/60 text-indigo-400 text-xs font-semibold uppercase tracking-wider">
          <Sparkles className="w-3.5 h-3.5" /> Reel Claim Cross-Check Engine
        </div>
        <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-100 tracking-tight">
          Audit Reel Claims Against Site Evidence
        </h2>
        <p className="text-slate-400 text-sm">
          Paste promotional caption text and optional site URL. ReelClaim extracts verifiable facts and matches them against published site pages.
        </p>
      </div>

      {/* Preset Demo Options */}
      <div className="space-y-2">
        <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Try Demo Scenarios:</span>
        <div className="flex flex-wrap gap-2">
          {PRESET_EXAMPLES.map((preset, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => handlePresetSelect(preset)}
              disabled={isLoading}
              className="text-xs px-3 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700/80 text-slate-300 border border-slate-700/60 transition-all cursor-pointer disabled:opacity-50"
            >
              {preset.label}
            </button>
          ))}
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Caption Textarea */}
        <div className="space-y-2">
          <label className="flex items-center gap-2 text-sm font-semibold text-slate-200">
            <FileText className="w-4 h-4 text-indigo-400" />
            Social Media Caption Text <span className="text-rose-400">*</span>
          </label>
          <textarea
            rows={4}
            value={caption}
            onChange={(e) => setCaption(e.target.value)}
            disabled={isLoading}
            placeholder="Paste reel caption, text overlay, or promotional copy (e.g. Boot.dev offers ₹999/mo membership with 30-day money back guarantee...)"
            className="w-full px-4 py-3 bg-slate-950/80 border border-slate-800 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm transition-all resize-y"
          />
        </div>

        {/* URL Input */}
        <div className="space-y-2">
          <label className="flex items-center gap-2 text-sm font-semibold text-slate-200">
            <LinkIcon className="w-4 h-4 text-indigo-400" />
            Promoted Site URL <span className="text-xs font-normal text-slate-400">(Optional if URL is inside caption)</span>
          </label>
          <input
            type="text"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            disabled={isLoading}
            placeholder="https://boot.dev/pricing"
            className="w-full px-4 py-2.5 bg-slate-950/80 border border-slate-800 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm transition-all"
          />
        </div>

        {/* Validation or Error Message */}
        {(validationError || error) && (
          <div className="flex items-center gap-2.5 p-3.5 rounded-xl bg-rose-950/40 border border-rose-900/60 text-rose-300 text-sm">
            <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
            <span>{validationError || error}</span>
          </div>
        )}

        {/* Submit Button */}
        <button
          type="submit"
          disabled={isLoading}
          className="w-full flex items-center justify-center gap-2 py-3.5 px-6 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-semibold rounded-xl shadow-lg shadow-indigo-950/50 transition-all cursor-pointer disabled:opacity-60 disabled:cursor-not-allowed"
        >
          {isLoading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>Analyzing & Verifying Reel...</span>
            </>
          ) : (
            <>
              <Search className="w-5 h-5" />
              <span>Run Reel Claim Audit</span>
            </>
          )}
        </button>
      </form>

      {/* Multi-step Live Loading Progress */}
      {isLoading && (
        <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 space-y-3">
          <div className="flex items-center justify-between text-xs text-slate-400 font-medium">
            <span className="uppercase tracking-wider">Audit Pipeline Progress</span>
            <span className="text-[11px] text-indigo-400">Connecting to server (waking up service if idle)...</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs">
            <div className={`p-2.5 rounded-lg border text-center transition-all ${getStepStatusClass('extracting')}`}>
              1. Extracting Claims
            </div>
            <div className={`p-2.5 rounded-lg border text-center transition-all ${getStepStatusClass('crawling')}`}>
              2. Crawling Site Facts
            </div>
            <div className={`p-2.5 rounded-lg border text-center transition-all ${getStepStatusClass('cross_checking')}`}>
              3. Cross-Checking Evidence
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
