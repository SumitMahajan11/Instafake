export type ClaimCategory = 
  | "price"
  | "certificate"
  | "partnership"
  | "eligibility"
  | "deadline"
  | "salary"
  | "discount"
  | "refund"
  | "other";

export type VerdictType = "confirmed" | "contradicted" | "partial" | "not_found";

export type CoverageStatus = "verified" | "partially_verified" | "unverified_no_data";

export interface Claim {
  category: ClaimCategory;
  text: string;
  confidence: "high" | "medium" | "low";
  source_type: "caption" | "comment";
}

export interface SiteFact {
  category: ClaimCategory;
  text: string;
  source_page: string;
  source_url: string;
}

export interface ClaimVerdict {
  claim_text: string;
  category: ClaimCategory;
  source_type: "caption" | "comment";
  verdict: VerdictType;
  evidence_text: string | null;
  source_url: string | null;
  reasoning: string;
}

export interface ScoreBreakdown {
  confirmed_count: number;
  partial_count: number;
  contradicted_count: number;
  not_found_count: number;
  addressed_claims: number;
  total_claims: number;
}

export interface CheckResponse {
  trust_score: number | null;
  coverage_status: CoverageStatus;
  summary_label: string;
  score_breakdown: ScoreBreakdown;
  verdicts: ClaimVerdict[];
}

export interface FullAuditRequest {
  caption: string;
  override_url?: string;
  gemini_api_key?: string;
}


export type CrawlStatus = "success" | "degraded" | "busy" | "overloaded" | "blocked" | "failed" | "no_url_found";

export interface FullAuditResponse {
  id?: string;
  created_at?: string;
  caption: string;
  promoted_site: string | null;
  claims: Claim[];
  crawl_status: CrawlStatus | string | null;
  check_result: CheckResponse | null;
}

export interface RecentAuditItem {
  id: string;
  created_at: string | null;
  caption: string;
  promoted_site: string | null;
  crawl_status: string | null;
  trust_score: number | null;
  coverage_status: string | null;
  summary_label: string | null;
  total_claims: number;
  status: string;
}

export interface RecentAuditsResponse {
  total: number;
  limit: number;
  offset: number;
  audits: RecentAuditItem[];
  persistence?: string;
}

export type ProgressStep = "idle" | "extracting" | "crawling" | "crawling_busy" | "cross_checking" | "complete" | "error";

