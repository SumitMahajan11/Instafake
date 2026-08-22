# ReelClaim — Backend Service (Phase 1 & Phase 2)

ReelClaim is a FastAPI-based backend service designed to audit promotional social media content.
- **Phase 1**: Claim Extraction Module — accepts reel captions and extracts promotional claims via Gemini LLM.
- **Phase 2**: Site Crawler Module — crawls promoted target websites, discovers key pages, and extracts verifiable facts per page.

---

## 📁 Project Structure

```
reelclaim-backend/
├── app/
│   ├── main.py              # FastAPI app with POST /extract-claims & POST /crawl-site
│   ├── extraction.py        # Core Phase 1 claim extraction logic
│   ├── crawler.py           # Core Phase 2 site crawler & fetch engine
│   ├── prompts/
│   │   ├── claim_extraction.txt   # Prompt template for claim extraction
│   │   └── fact_extraction.txt    # Prompt template for site fact extraction
│   └── models.py            # Pydantic schemas for request & response models
├── tests/
│   ├── test_extraction.py   # Live test suite for Phase 1
│   ├── test_crawler.py      # Live test suite for Phase 2 (5 diverse websites)
│   └── test_api.py          # FastAPI endpoint integration test
├── .env.example
├── .env                     # Local environment file
├── requirements.txt         # Project dependencies
└── README.md                # Documentation & run guide
```

---

## ⚙️ Setup Instructions

### 1. Environment Setup

Create a `.env` file in `reelclaim-backend`:

```bash
cp .env.example .env
```

Set your Gemini API key in `.env`:
```env
GEMINI_API_KEY=your_actual_gemini_api_key
GEMINI_MODEL=gemini-3.5-flash-lite
```

### 2. Install Dependencies & Playwright Browsers

```bash
pip install -r requirements.txt
python -m playwright install chromium
```

---

## 🚀 Running the Server

Start the FastAPI development server:

```bash
uvicorn app.main:app --reload --port 8000
```

- **Base URL**: `http://localhost:8000`
- **Interactive OpenAPI Specs**: `http://localhost:8000/docs`

---

## 📡 API Endpoints

### 1. `POST /extract-claims` (Phase 1)

#### Request Body
```json
{
  "caption": "🔥 FREE 3-Month AI/ML Internship Opportunity! Get official Google AI training and a verified certificate of completion. Apply now at https://google.com/careers"
}
```

---

### 2. `POST /crawl-site` (Phase 2)

#### Request Body
```json
{
  "url": "https://example.com"
}
```

#### Response Body
```json
{
  "site_url": "https://example.com",
  "pages_found": ["home"],
  "pages_missing": ["pricing", "terms", "faq", "registration", "refund_policy"],
  "facts": [
    {
      "category": "other",
      "text": "This domain is intended for use in documentation examples without needing prior permission.",
      "source_page": "home",
      "source_url": "https://example.com"
    }
  ],
  "crawl_status": "success"
}
```

---

## 🧪 Running Verification Tests

Run the full suite of live crawler and extraction tests:

```bash
python tests/test_crawler.py
python tests/test_extraction.py
pytest -v
```

---

## 🌐 Crawl Fetch Strategy (Two-Tier Architecture)

1. **Tier 1 (Requests + BeautifulSoup)**: Executes fast HTTP requests. Strips tags and extracts clean text.
2. **Tier 2 (Playwright Chromium Fallback)**: Automatically triggered if Tier 1 encounters a client-rendered SPA JS shell (e.g. `<div id="root">` with < 200 text characters).
3. **Graceful Blocking**: If a site responds with `403 Forbidden`, `401`, `429`, Cloudflare anti-bot challenge, or is disallowed by `robots.txt`, the status resolves cleanly to `"crawl_status": "blocked"` with whatever partial data was collected.
