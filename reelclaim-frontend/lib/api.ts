import { FullAuditRequest, FullAuditResponse, ProgressStep } from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://reelclaim-api.onrender.com';

const RETRY_DELAYS_MS = [3000, 5000, 8000, 10000]; // 3s, 5s, 8s, 10s (cumulative ~26s window)

export async function auditReel(
  caption: string,
  overrideUrl?: string,
  onStepChange?: (step: ProgressStep, details?: { retryAttempt?: number; maxRetries?: number; nextDelaySec?: number }) => void
): Promise<FullAuditResponse> {
  if (onStepChange) onStepChange('extracting');

  const payload: FullAuditRequest = {
    caption,
    override_url: overrideUrl && overrideUrl.trim().length > 0 ? overrideUrl.trim() : undefined,
  };

  const executeRequest = async (): Promise<FullAuditResponse> => {
    const response = await fetch(`${API_BASE_URL}/audit-reel`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Server returned error status ${response.status}`);
    }

    return await response.json();
  };

  // Step feedback timer during initial extraction / crawl
  let currentStepState: ProgressStep = 'extracting';
  const stepTimer1 = setTimeout(() => {
    if (currentStepState === 'extracting') {
      currentStepState = 'crawling';
      if (onStepChange) onStepChange('crawling');
    }
  }, 2500);

  const stepTimer2 = setTimeout(() => {
    if (currentStepState === 'crawling') {
      currentStepState = 'cross_checking';
      if (onStepChange) onStepChange('cross_checking');
    }
  }, 8000);

  try {
    let result = await executeRequest();
    clearTimeout(stepTimer1);
    clearTimeout(stepTimer2);

    // If initial response indicates browser concurrency lock is busy, initiate progressive backoff retries
    let attempt = 0;
    while (result.crawl_status === 'busy' && attempt < RETRY_DELAYS_MS.length) {
      const delayMs = RETRY_DELAYS_MS[attempt];
      const nextDelaySec = Math.round(delayMs / 1000);
      attempt++;

      if (onStepChange) {
        onStepChange('crawling_busy', {
          retryAttempt: attempt,
          maxRetries: RETRY_DELAYS_MS.length,
          nextDelaySec,
        });
      }

      await new Promise((resolve) => setTimeout(resolve, delayMs));

      if (onStepChange) onStepChange('crawling');
      result = await executeRequest();
    }

    return result;
  } catch (err: any) {
    clearTimeout(stepTimer1);
    clearTimeout(stepTimer2);
    throw new Error(err.message || 'Failed to connect to ReelClaim audit service');
  }
}

