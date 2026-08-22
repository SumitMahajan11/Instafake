import { FullAuditRequest, FullAuditResponse } from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function auditReel(
  caption: string,
  overrideUrl?: string,
  onStepChange?: (step: 'extracting' | 'crawling' | 'cross_checking') => void
): Promise<FullAuditResponse> {
  if (onStepChange) onStepChange('extracting');

  // Small delay simulation for step-by-step feedback to user during long backend LLM/crawl pipeline
  const stepTimer1 = setTimeout(() => {
    if (onStepChange) onStepChange('crawling');
  }, 2000);

  const stepTimer2 = setTimeout(() => {
    if (onStepChange) onStepChange('cross_checking');
  }, 6000);

  try {
    const payload: FullAuditRequest = {
      caption,
      override_url: overrideUrl && overrideUrl.trim().length > 0 ? overrideUrl.trim() : undefined,
    };

    const response = await fetch(`${API_BASE_URL}/audit-reel`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    clearTimeout(stepTimer1);
    clearTimeout(stepTimer2);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Server returned error status ${response.status}`);
    }

    const data: FullAuditResponse = await response.json();
    return data;
  } catch (err: any) {
    clearTimeout(stepTimer1);
    clearTimeout(stepTimer2);
    throw new Error(err.message || 'Failed to connect to ReelClaim audit service');
  }
}
