# 🎬 ScriptStream

**AI-powered YouTube script generator** that researches trending content across YouTube, Reddit, and the web — then writes you a ready-to-record script.

ScriptStream uses the **PRAT framework** (Perceive → Reason → Act → Track) to analyze real content, surface trending topics, and generate structured video scripts tailored to your niche.

---

## ✨ Features

- **Two-Step Generation** — First discover trending topic ideas, then generate a full script for your chosen topic
- **Multi-Source Research** — Scrapes and analyzes content from YouTube, Reddit, and generic web pages
- **Category Presets** — Quick-start with built-in presets for Technology, Gaming, Finance, Education, and Lifestyle
- **Configurable Output** — Choose video length, number of topic suggestions, and research time window
- **B-Roll & On-Screen Text Cues** — Toggle optional `[B-Roll: ...]` and `[TEXT: ...]` markers in your script
- **Script Actions** — Copy to clipboard or download as `.txt` with one click
- **Research History** — Every generated script is saved and browsable from the History page
- **LLM-Powered** — Uses Groq's Llama 3.3 70B model for fast, high-quality generation

---

## 🏗️ Tech Stack

| Layer    | Technology                          |
| -------- | ----------------------------------- |
| Frontend | Next.js 16, React 19, TypeScript    |
| Backend  | Python, FastAPI, Pydantic           |
| LLM      | Groq API (Llama 3.3 70B Versatile)  |
| Scraping | Requests, BeautifulSoup4, lxml      |
| Storage  | Local JSON (append-only)            |

---

## 🚀 Getting Started

### Prerequisites

- **Node.js** 18+
- **Python** 3.10+
- A free **[Groq API key](https://console.groq.com)**

### 1. Clone the repo

```bash
git clone https://github.com/samyub/ScriptStream.git
cd ScriptStream
```

### 2. Backend setup

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

Create a `.env` file in the `backend/` directory:

```env
GROQ_API_KEY=your_groq_api_key_here
```

Start the API server:

```bash
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend setup

```bash
cd frontend
npm install
npm run dev
```

### 4. Open in browser

Navigate to **[http://localhost:3000](http://localhost:3000)** and start generating scripts!

---

## 📖 How It Works

ScriptStream follows the **PRAT framework**:

1. **Perceive** — Parses your prompt, extracts keywords, classifies intent, and builds a research plan
2. **Reason** — Determines source strategy, expands search space, and applies time filters
3. **Act** — Scrapes pages, normalizes content, ranks results by engagement & relevance, and generates the script
4. **Track** — Saves every run to local JSON storage for later review

### Workflow

```
Enter Prompt / Category ──► Generate Topics ──► Pick a Topic ──► Full Script
```

---

## 📁 Project Structure

```
ScriptStream/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── routes/
│   │   │   └── research.py      # API endpoints (/topics, /script, /research, /history)
│   │   ├── core/
│   │   │   ├── pipeline.py      # PRAT framework orchestration
│   │   │   ├── ranking.py       # Content scoring & ranking
│   │   │   ├── markdown.py      # Script generation via LLM
│   │   │   ├── storage.py       # JSON file persistence
│   │   │   └── errors.py        # Custom error classes
│   │   └── sources/
│   │       ├── base.py          # ContentItem schema
│   │       ├── youtube.py       # YouTube scraper
│   │       ├── reddit.py        # Reddit scraper
│   │       └── generic.py       # Generic web scraper
│   ├── data/                    # Local JSON storage
│   └── requirements.txt
├── frontend/
│   └── src/app/
│       ├── page.tsx             # Script generator (main dashboard)
│       ├── history/page.tsx     # Research history viewer
│       ├── layout.tsx           # App shell & navigation
│       └── globals.css          # Design system & styles
└── README.md
```

---

## 🔌 API Endpoints

| Method | Endpoint              | Description                          |
| ------ | --------------------- | ------------------------------------ |
| POST   | `/api/topics`         | Generate trending topic suggestions  |
| POST   | `/api/script`         | Generate a full script for a topic   |
| POST   | `/api/research`       | Run full PRAT pipeline (legacy)      |
| GET    | `/api/history`        | List all past research runs          |
| GET    | `/api/history/{id}`   | Get details of a specific run        |
| GET    | `/health`             | Health check                         |

---

## 📄 License

This project is for personal use.
