import React, { useState, useEffect } from 'react';
import { Search, Loader2, AlertCircle, Link as LinkIcon, FileText, Info, Key } from 'lucide-react';
import { ProgressStep } from '@/lib/types';

interface AuditFormProps {
  onSubmit: (caption: string, url: string, apiKey?: string) => void;
  isLoading: boolean;
  currentStep: ProgressStep;
  retryDetails?: { retryAttempt?: number; maxRetries?: number; nextDelaySec?: number } | null;
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

export const AuditForm: React.FC<AuditFormProps> = ({ onSubmit, isLoading, currentStep, retryDetails, error }) => {
  const [caption, setCaption] = useState<string>('');
  const [url, setUrl] = useState<string>('');
  const [apiKey, setApiKey] = useState<string>('');
  const [showAdvanced, setShowAdvanced] = useState<boolean>(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [elapsedSeconds, setElapsedSeconds] = useState<number>(0);

  // Timer for smooth rotating progress status & cold-start notice
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isLoading) {
      setElapsedSeconds(0);
      interval = setInterval(() => {
        setElapsedSeconds((prev) => prev + 1);
      }, 1000);
    } else {
      setElapsedSeconds(0);
    }
    return () => clearInterval(interval);
  }, [isLoading]);

  // Dynamic rotating status message based on measured timings (HTTP: 2-5s, SPA: 18-28s, Cold start: 50s+)
  const getStatusMessage = (): string => {
    if (currentStep === 'crawling_busy') {
      return `Server busy — retrying (attempt ${retryDetails?.retryAttempt || 1} of ${retryDetails?.maxRetries || 4}) in ${retryDetails?.nextDelaySec || 3}s... (Usually resolves shortly)`;
    }

    if (elapsedSeconds < 3) {
      return 'Extracting claims from social caption...';
    } else if (elapsedSeconds < 7) {
      return 'Loading page & checking site structure...';
    } else if (elapsedSeconds < 15) {
      return 'Crawling DOM facts with Playwright engine...';
    } else if (elapsedSeconds < 24) {
      return 'Cross-checking claims with Gemini...';
    } else {
      return 'Finalizing claim verification report...';
    }
  };

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

    onSubmit(caption.trim(), url.trim(), apiKey.trim());
  };

  const handlePresetSelect = (preset: typeof PRESET_EXAMPLES[0]) => {
    setCaption(preset.caption);
    setUrl(preset.url);
    setValidationError(null);
  };

  const getStepStatusStyle = (step: 'extracting' | 'crawling' | 'cross_checking'): React.CSSProperties => {
    if (currentStep === step || (step === 'crawling' && currentStep === 'crawling_busy')) {
      return {
        backgroundColor: 'var(--bg-elevated)',
        borderColor: 'var(--border-bright)',
        color: 'var(--text-primary)',
        fontWeight: '600',
      };
    }
    const steps: Array<'extracting' | 'crawling' | 'cross_checking'> = ['extracting', 'crawling', 'cross_checking'];
    const currentIndex = steps.indexOf(currentStep === 'crawling_busy' ? 'crawling' : (currentStep as any));
    const stepIndex = steps.indexOf(step);
    if (stepIndex < currentIndex) {
      return {
        backgroundColor: 'var(--verdict-verified-bg)',
        borderColor: 'var(--verdict-verified-border)',
        color: 'var(--verdict-verified-text)',
      };
    }
    return {
      backgroundColor: 'var(--bg-card-subtle)',
      borderColor: 'var(--border-subtle)',
      color: 'var(--text-muted)',
    };
  };

  return (
    <div className="w-full space-y-6">
      {/* Header Info — plain small-caps mono eyebrow, no pill badge */}
      <div className="space-y-2">
        <span
          className="text-[10px] uppercase tracking-widest font-semibold"
          style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', letterSpacing: '0.12em' }}
        >
          Reel Claim Intake
        </span>
        <h2
          className="text-lg font-bold tracking-tight leading-snug"
          style={{ fontFamily: 'var(--font-serif)', color: 'var(--text-primary)' }}
        >
          Audit Claims Against Site Evidence
        </h2>
        <p className="text-xs leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
          Paste a promotional caption and optional URL. ReelClaim extracts verifiable claims and cross-checks them against published site pages.
        </p>
      </div>

      {/* Preset Demo Options */}
      <div className="space-y-2">
        <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>Try Demo Scenarios:</span>
        <div className="flex flex-wrap gap-1.5">
          {PRESET_EXAMPLES.map((preset, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => handlePresetSelect(preset)}
              disabled={isLoading}
              className="text-[11px] px-2.5 py-1 rounded-lg border transition-all cursor-pointer disabled:opacity-50 hover:opacity-80"
              style={{
                backgroundColor: 'var(--bg-card-subtle)',
                borderColor: 'var(--border-subtle)',
                color: 'var(--text-primary)',
              }}
            >
              {preset.label}
            </button>
          ))}
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Caption Textarea */}
        <div className="space-y-1.5">
          <label className="flex items-center gap-1.5 text-xs font-semibold" style={{ color: 'var(--text-primary)' }}>
            <FileText className="w-3.5 h-3.5" style={{ color: 'var(--text-accent)' }} />
            Social Media Caption Text <span className="text-rose-500">*</span>
          </label>
          <textarea
            rows={4}
            value={caption}
            onChange={(e) => setCaption(e.target.value)}
            disabled={isLoading}
            placeholder="Paste reel caption, text overlay, or promotional copy..."
            className="w-full px-3 py-2.5 border rounded-xl text-xs transition-all resize-y focus:outline-none focus:ring-2"
            style={{
              backgroundColor: 'var(--bg-card-subtle)',
              borderColor: 'var(--border-med)',
              color: 'var(--text-primary)',
            }}
          />
        </div>

        {/* URL Input */}
        <div className="space-y-1.5">
          <label className="flex items-center gap-1.5 text-xs font-semibold" style={{ color: 'var(--text-primary)' }}>
            <LinkIcon className="w-3.5 h-3.5" style={{ color: 'var(--text-accent)' }} />
            Promoted Site URL <span className="text-[10px] font-normal" style={{ color: 'var(--text-muted)' }}>(Optional)</span>
          </label>
          <input
            type="text"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            disabled={isLoading}
            placeholder="https://boot.dev/pricing"
            className="w-full px-3 py-2 border rounded-xl text-xs transition-all focus:outline-none focus:ring-2"
            style={{
              backgroundColor: 'var(--bg-card-subtle)',
              borderColor: 'var(--border-med)',
              color: 'var(--text-primary)',
            }}
          />
        </div>

        {/* Collapsible BYOK Section */}
        <div className="space-y-2 pt-1 border-t" style={{ borderColor: 'var(--border-subtle)' }}>
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="flex items-center gap-1.5 text-xs font-semibold cursor-pointer hover:opacity-80 transition-opacity"
            style={{ color: 'var(--text-secondary)' }}
          >
            <Key className="w-3.5 h-3.5" style={{ color: 'var(--text-accent)' }} />
            <span>Use your own key (BYOK)</span>
            <span className="text-[10px] font-normal" style={{ color: 'var(--text-muted)' }}>
              {showAdvanced ? '▲ hide' : '▼ optional'}
            </span>
          </button>

          {showAdvanced && (
            <div className="p-3 rounded-xl border space-y-2 animate-fadeIn" style={{ backgroundColor: 'var(--bg-card-subtle)', borderColor: 'var(--border-med)' }}>
              <label className="block text-xs font-semibold" style={{ color: 'var(--text-primary)' }}>
                Google Gemini API Key
              </label>
              <input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                disabled={isLoading}
                placeholder="AIzaSy..."
                className="w-full px-3 py-2 border rounded-xl text-xs font-mono transition-all focus:outline-none focus:ring-2"
                style={{
                  backgroundColor: 'var(--bg)',
                  borderColor: 'var(--border-med)',
                  color: 'var(--text-primary)',
                }}
              />
              <div className="flex items-start gap-1.5 text-[11px] leading-snug" style={{ color: 'var(--text-muted)' }}>
                <Info className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" style={{ color: 'var(--text-accent)' }} />
                <span>
                  Avoids shared rate limits (20 RPM). Required for high-volume or self-hosted use. Key is stored only in memory for this session and is never persisted.
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Validation or Error Message */}
        {(validationError || error) && (
          <div className="flex items-center gap-2.5 p-3.5 rounded-xl bg-rose-950/40 border border-rose-900/60 text-rose-300 text-sm">
            <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
            <span>{validationError || error}</span>
          </div>
        )}

        {/* Submit Button — flat solid fill, NO gradient */}
        <button
          type="submit"
          disabled={isLoading}
          className="w-full flex items-center justify-center gap-2 py-2.5 px-5 font-semibold text-xs rounded cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed hover:opacity-85"
          style={{
            backgroundColor: 'var(--accent-brand)',
            color: 'var(--bg)',
            fontFamily: 'var(--font-mono)',
            letterSpacing: '0.04em',
            border: 'none',
          }}
        >
          {isLoading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>
                {currentStep === 'crawling_busy'
                  ? `Retrying (${retryDetails?.retryAttempt || 1}/${retryDetails?.maxRetries || 4})...`
                  : getStatusMessage()}
              </span>
            </>
          ) : (
            <>
              <Search className="w-3.5 h-3.5" />
              <span>Open the case →</span>
            </>
          )}
        </button>
      </form>


      {/* Multi-step Live Loading Progress */}
      {isLoading && (
        <div
          className="p-4 rounded-xl border space-y-3.5 animate-fadeIn"
          style={{
            backgroundColor: 'var(--bg-card-subtle)',
            borderColor: 'var(--border-med)',
          }}
        >
          <div className="flex items-center justify-between text-xs font-medium" style={{ color: 'var(--text-muted)' }}>
            <span className="uppercase tracking-wider text-[10px]">Pipeline Progress</span>
            <span className="text-xs font-semibold flex items-center gap-1.5" style={{ color: 'var(--text-accent)' }}>
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              {getStatusMessage()}
            </span>
          </div>

          {/* Animated Progress Bar — flat solid, no gradient */}
          <div
            className="w-full h-1.5 overflow-hidden"
            style={{
              backgroundColor: 'var(--bg-elevated)',
              borderRadius: '2px',
            }}
          >
            <div
              className="h-full"
              style={{
                width: `${Math.min(95, Math.max(8, elapsedSeconds * 4))}%`,
                backgroundColor: 'var(--accent-brand)',
                transition: 'width 0.5s ease-out',
                borderRadius: '2px',
              }}
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-1.5 text-[11px]">
            <div className="p-2 rounded border text-center" style={getStepStatusStyle('extracting')}>
              1. Extracting
            </div>
            <div className="p-2 rounded border text-center" style={getStepStatusStyle('crawling')}>
              {currentStep === 'crawling_busy'
                ? `2. Busy (${retryDetails?.retryAttempt}/${retryDetails?.maxRetries})`
                : '2. Crawling'}
            </div>
            <div className="p-2 rounded border text-center" style={getStepStatusStyle('cross_checking')}>
              3. Checking
            </div>
          </div>

          {/* Informational Crawl Timing Note */}
          {elapsedSeconds >= 6 && currentStep !== 'crawling_busy' && (
            <div
              className="flex items-center gap-2 text-[11px] p-2.5 rounded-lg border transition-all"
              style={{
                backgroundColor: 'var(--bg)',
                borderColor: 'var(--border-subtle)',
                color: 'var(--text-secondary)',
              }}
            >
              <Info className="w-4 h-4 flex-shrink-0" style={{ color: 'var(--text-accent)' }} />
              <span>
                {elapsedSeconds < 15 ? (
                  'Full SPA crawls typically take 18–28s.'
                ) : (
                  'Full SPA crawls typically take 18–28s. Server may take extra time if waking from idle.'
                )}
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
