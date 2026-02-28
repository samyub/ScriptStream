# Dyut Website Research Agent (PRAT Framework)

## Product + Technical Specification (Next.js Frontend + Python Backend)

**Goal:** A local-only web dashboard for YouTubers that generates
actionable trend and content opportunity research from any URL
(optimized for YouTube + Reddit) and outputs a single Markdown report
per request.

------------------------------------------------------------------------

## Architecture Overview

-   Frontend: Next.js (Dashboard UI)
-   Backend: Python (FastAPI)
-   Execution: Synchronous request/response
-   Storage: Local JSON file (append-only)
-   No authentication
-   No official APIs
-   No citations in output

------------------------------------------------------------------------

# 1. PRAT Framework

## P --- Perceive

-   Parse user prompt
-   Extract keywords
-   Classify intent (trend discovery, influencer ranking, content
    ideation)
-   Expand semantic keyword set
-   Build research plan

## R --- Reason

-   Determine source strategy (YouTube, Reddit, generic web)
-   Expand search space
-   Apply time filters
-   Score candidates based on:
    -   Engagement proxy
    -   Recency
    -   Keyword match

## A --- Act

-   Scrape pages
-   Normalize into unified ContentItem schema
-   Rank items
-   Generate structured Markdown report

## T --- Track

-   Append each run to local JSON store
-   Store:
    -   Inputs
    -   Extracted keywords
    -   Ranked results
    -   Generated Markdown

------------------------------------------------------------------------

# 2. Backend (Python - FastAPI)

## Folder Structure

backend/ │ ├── app/ │ ├── main.py │ ├── routes/ │ │ └── research.py │
├── core/ │ │ ├── pipeline.py │ │ ├── ranking.py │ │ ├── markdown.py │ │
├── storage.py │ │ └── errors.py │ ├── sources/ │ │ ├── base.py │ │ ├──
youtube.py │ │ ├── reddit.py │ │ └── generic.py │ └── data/ └──
research_history.json

------------------------------------------------------------------------

## API Endpoint

POST /api/research

Request: - target_urls: list\[str\] - prompt: str - time_window:
optional (24h, 7d, 14d, 30d) - category: optional - num_results: 1--20 -
include_debug: bool

Response: - report_markdown: str - results: structured ranked list -
stored_record_id: str

------------------------------------------------------------------------

# 3. Data Model

## ContentItem

-   id
-   source (youtube \| reddit \| generic)
-   url
-   title
-   author
-   published_at
-   extracted_text
-   engagement metrics
-   raw metadata

## ResearchRunRecord

-   id
-   created_at
-   inputs
-   plan
-   selected_results
-   report_markdown

------------------------------------------------------------------------

# 4. Frontend (Next.js)

## Routes

-   /dashboard
-   /history
-   /history/\[id\]

## Components

-   ResearchForm
-   RunStatus
-   MarkdownViewer
-   HistoryTable

## UX Requirements

-   Inline validation
-   Presets
-   Copy Markdown
-   Download .md
-   Clear error handling

------------------------------------------------------------------------

# 5. Local Deployment

Backend: uvicorn app.main:app --reload --port 8000

Frontend: npm run dev

------------------------------------------------------------------------

# 6. Acceptance Criteria

-   Synchronous Markdown research generation
-   Structured output
-   Persistent JSON history
-   Fully local execution
