"use client";

import { useState } from "react";

const API = "http://localhost:8000/api";

const CATEGORIES = [
  { value: "", label: "— Select a category —" },
  { value: "technology", label: "🧠 Technology" },
  { value: "finance", label: "💰 Finance & Investing" },
  { value: "gaming", label: "🎮 Gaming" },
  { value: "entertainment", label: "🎭 Entertainment" },
  { value: "lifestyle", label: "✨ Lifestyle" },
  { value: "education", label: "📚 Education" },
];

const PRESETS = [
  { label: "🔥 Trending AI", prompt: "What are the hottest AI tools and topics right now?", category: "technology" },
  { label: "🎮 Gaming Trends", prompt: "What gaming content is blowing up on YouTube?", category: "gaming" },
  { label: "💰 Finance Niche", prompt: "What personal finance topics are resonating with audiences?", category: "finance" },
  { label: "📚 How-To Content", prompt: "What high-value tutorial topics are getting traction?", category: "education" },
  { label: "✨ Lifestyle Trends", prompt: "What lifestyle trends are captivating viewers?", category: "lifestyle" },
];

type Step = "form" | "topics" | "script";

interface TopicsResult {
  topics: string;
  context_snapshot: string;
  keywords: string[];
}

interface ScriptResult {
  script: string;
  stored_record_id: string;
}

export default function DashboardPage() {
  // Form state
  const [prompt, setPrompt] = useState("");
  const [category, setCategory] = useState("");
  const [urls, setUrls] = useState<string[]>([""]);
  const [numTitles, setNumTitles] = useState(3);
  const [videoDuration, setVideoDuration] = useState("5 min");
  const [timeWindow, setTimeWindow] = useState("7d");
  const [brollEnabled, setBrollEnabled] = useState(false);
  const [onscreenEnabled, setOnscreenEnabled] = useState(false);

  // State machine
  const [step, setStep] = useState<Step>("form");
  const [loading, setLoading] = useState(false);
  const [loadingMsg, setLoadingMsg] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [toast, setToast] = useState<{ message: string; type: string } | null>(null);

  // Data
  const [topicsResult, setTopicsResult] = useState<TopicsResult | null>(null);
  const [parsedTopics, setParsedTopics] = useState<string[]>([]);
  const [selectedTopic, setSelectedTopic] = useState("");
  const [scriptResult, setScriptResult] = useState<ScriptResult | null>(null);

  const showToast = (message: string, type = "success") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  const addUrl = () => setUrls([...urls, ""]);
  const removeUrl = (i: number) => setUrls(urls.filter((_, idx) => idx !== i));
  const updateUrl = (i: number, val: string) => {
    const copy = [...urls]; copy[i] = val; setUrls(copy);
  };

  const applyPreset = (preset: typeof PRESETS[0]) => {
    setPrompt(preset.prompt);
    setCategory(preset.category);
  };

  const parseTopics = (text: string): string[] => {
    return text
      .split("\n")
      .map(line => line.replace(/^\d+\.\s*/, "").trim())
      .filter(line => line.length > 0);
  };

  // ── Step 1: Generate Topics ──
  const handleGenerateTopics = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim() && !category) {
      setError("Please enter a topic or select a category.");
      return;
    }

    setLoading(true);
    setError(null);
    setLoadingMsg("Researching trending content...");

    try {
      const res = await fetch(`${API}/topics`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt: prompt.trim(),
          category,
          target_urls: urls.filter(u => u.trim()),
          num_titles: numTitles,
          time_window: timeWindow,
        }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || `Request failed (${res.status})`);
      }

      const data: TopicsResult = await res.json();
      const topics = parseTopics(data.topics);
      setTopicsResult(data);
      setParsedTopics(topics);

      if (numTitles === 1 && topics.length === 1) {
        // Auto-proceed to script for single title
        await generateScript(topics[0], data.context_snapshot);
      } else {
        setStep("topics");
        setSelectedTopic(topics[0] ?? "");
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
      setLoadingMsg("");
    }
  };

  // ── Step 2: Generate Script ──
  const generateScript = async (topic: string, contextSnapshot?: string) => {
    setLoading(true);
    setLoadingMsg("Writing your script...");
    setError(null);

    try {
      const res = await fetch(`${API}/script`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          topic,
          category,
          video_duration: videoDuration,
          broll_enabled: brollEnabled,
          onscreen_text_enabled: onscreenEnabled,
          context_snapshot: contextSnapshot ?? topicsResult?.context_snapshot ?? "",
          original_prompt: prompt,
        }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || `Request failed (${res.status})`);
      }

      const data: ScriptResult = await res.json();
      setScriptResult(data);
      setStep("script");
      showToast("Script generated!");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
      setLoadingMsg("");
    }
  };

  const handleScriptGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTopic) return;
    await generateScript(selectedTopic);
  };

  const copyScript = () => {
    if (scriptResult?.script) {
      navigator.clipboard.writeText(scriptResult.script);
      showToast("Script copied to clipboard!");
    }
  };

  const downloadScript = () => {
    if (scriptResult?.script) {
      const blob = new Blob([scriptResult.script], { type: "text/plain" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `script-${Date.now()}.txt`;
      a.click();
      URL.revokeObjectURL(url);
      showToast("Script downloaded!");
    }
  };

  const reset = () => {
    setStep("form");
    setTopicsResult(null);
    setParsedTopics([]);
    setSelectedTopic("");
    setScriptResult(null);
    setError(null);
  };

  return (
    <>
      <div className="page-header">
        <h2>🎬 Script Generator</h2>
        <p>Research trending topics and generate a ready-to-record YouTube script</p>
      </div>

      {/* ── FORM STEP ── */}
      {step === "form" && (
        <>
          <div className="presets">
            {PRESETS.map((p, i) => (
              <button key={i} className="preset-chip" onClick={() => applyPreset(p)}>
                {p.label}
              </button>
            ))}
          </div>

          <div className="card">
            <form onSubmit={handleGenerateTopics}>
              <div className="form-group">
                <label>Video Topic / Prompt <span style={{ color: "var(--text-muted)", fontWeight: 400 }}>(optional if category selected)</span></label>
                <textarea
                  className="form-textarea"
                  placeholder="e.g. 'The truth about passive income in 2025' — leave blank to use category only"
                  value={prompt}
                  onChange={e => setPrompt(e.target.value)}
                  id="research-prompt"
                />
              </div>

              <div className="form-group">
                <label>Category <span style={{ color: "var(--text-muted)", fontWeight: 400 }}>(required if no prompt)</span></label>
                <select className="form-select" value={category} onChange={e => setCategory(e.target.value)}>
                  {CATEGORIES.map(c => (
                    <option key={c.value} value={c.value}>{c.label}</option>
                  ))}
                </select>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Number of Topics</label>
                  <select className="form-select" value={numTitles} onChange={e => setNumTitles(Number(e.target.value))}>
                    <option value={1}>1 (auto-write script)</option>
                    <option value={2}>2</option>
                    <option value={3}>3</option>
                    <option value={4}>4</option>
                    <option value={5}>5</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Video Length</label>
                  <select className="form-select" value={videoDuration} onChange={e => setVideoDuration(e.target.value)}>
                    <option value="3 min">3 min</option>
                    <option value="5 min">5 min</option>
                    <option value="8 min">8 min</option>
                    <option value="10 min">10 min</option>
                    <option value="15 min">15 min</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Time Window</label>
                  <select className="form-select" value={timeWindow} onChange={e => setTimeWindow(e.target.value)}>
                    <option value="24h">Last 24 hours</option>
                    <option value="7d">Last 7 days</option>
                    <option value="14d">Last 14 days</option>
                    <option value="30d">Last 30 days</option>
                  </select>
                </div>
              </div>

              {/* Toggles */}
              <div className="form-row" style={{ gap: 16 }}>
                <div className="form-group toggle-group">
                  <label>B-Roll Suggestions</label>
                  <div className="toggle-row">
                    <button
                      type="button"
                      className={`toggle-btn ${brollEnabled ? "active" : ""}`}
                      onClick={() => setBrollEnabled(!brollEnabled)}
                      id="toggle-broll"
                    >
                      {brollEnabled ? "✅ On" : "Off"}
                    </button>
                    <span className="toggle-hint">Adds [B-Roll: ...] cues in script</span>
                  </div>
                </div>
                <div className="form-group toggle-group">
                  <label>On-Screen Text Cues</label>
                  <div className="toggle-row">
                    <button
                      type="button"
                      className={`toggle-btn ${onscreenEnabled ? "active" : ""}`}
                      onClick={() => setOnscreenEnabled(!onscreenEnabled)}
                      id="toggle-onscreen"
                    >
                      {onscreenEnabled ? "✅ On" : "Off"}
                    </button>
                    <span className="toggle-hint">Adds [TEXT: ...] cues in script</span>
                  </div>
                </div>
              </div>

              <div className="form-group">
                <label>Target URLs <span style={{ color: "var(--text-muted)", fontWeight: 400 }}>(optional — paste YouTube/Reddit links for targeted research)</span></label>
                <div className="url-list">
                  {urls.map((url, i) => (
                    <div key={i} className="url-row">
                      <input
                        className="form-input"
                        type="url"
                        placeholder="https://youtube.com/... or https://reddit.com/..."
                        value={url}
                        onChange={e => updateUrl(i, e.target.value)}
                      />
                      {urls.length > 1 && (
                        <button type="button" className="btn-remove-url" onClick={() => removeUrl(i)}>×</button>
                      )}
                    </div>
                  ))}
                  <button type="button" className="btn-add-url" onClick={addUrl}>+ Add URL</button>
                </div>
              </div>

              <button
                type="submit"
                className="btn btn-primary"
                disabled={loading || (!prompt.trim() && !category)}
                id="submit-research"
              >
                {loading ? loadingMsg || "Working..." : "🔍 Generate Topics →"}
              </button>
            </form>
          </div>
        </>
      )}

      {/* ── TOPICS STEP ── */}
      {step === "topics" && (
        <div className="card">
          <div className="page-header" style={{ marginBottom: 16 }}>
            <h2 style={{ fontSize: "1.2rem" }}>📋 Choose a Topic to Script</h2>
            <p>Pick the one that fits your channel best — we&apos;ll write the full script for it.</p>
          </div>

          <form onSubmit={handleScriptGenerate}>
            <div className="topics-list">
              {parsedTopics.map((topic, i) => (
                <button
                  key={i}
                  type="button"
                  className={`topic-card ${selectedTopic === topic ? "selected" : ""}`}
                  onClick={() => setSelectedTopic(topic)}
                >
                  <span className="topic-num">{i + 1}</span>
                  <span className="topic-title">{topic}</span>
                </button>
              ))}
            </div>

            {selectedTopic && (
              <div className="selected-topic-display">
                Selected: <strong>{selectedTopic}</strong>
              </div>
            )}

            <div style={{ display: "flex", gap: 12, marginTop: 20 }}>
              <button type="button" className="btn btn-secondary" onClick={reset}>
                ← Start Over
              </button>
              <button
                type="submit"
                className="btn btn-primary"
                disabled={!selectedTopic || loading}
                id="submit-script"
              >
                {loading ? "Writing script..." : `🎬 Write Script`}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* ── SCRIPT STEP ── */}
      {step === "script" && scriptResult && (
        <div className="markdown-viewer">
          <div className="markdown-actions">
            <button className="btn btn-secondary btn-sm" onClick={reset}>← New Script</button>
            <button className="btn btn-secondary btn-sm" onClick={copyScript} id="copy-markdown">
              📋 Copy Script
            </button>
            <button className="btn btn-secondary btn-sm" onClick={downloadScript} id="download-markdown">
              ⬇️ Download Script
            </button>
            <span className="badge badge-emerald" style={{ marginLeft: "auto" }}>
              ID: {scriptResult.stored_record_id.slice(0, 8)}
            </span>
          </div>
          <div
            className="markdown-content"
            dangerouslySetInnerHTML={{ __html: renderScript(scriptResult.script) }}
          />
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="card" style={{ marginTop: 24 }}>
          <div className="run-status">
            <div className="spinner" />
            <div className="status-text">{loadingMsg || "Working..."}</div>
            <div className="status-sub">Perceive → Reason → Act → Track</div>
            <div className="pulse-bar" />
          </div>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="error-box">
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Toast */}
      {toast && (
        <div className={`toast toast-${toast.type}`}>{toast.message}</div>
      )}
    </>
  );
}

/** Render the script with section label highlighting */
function renderScript(text: string): string {
  // Escape HTML
  let html = text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  // Highlight section labels like [HOOK], [INTRODUCTION], etc.
  html = html.replace(
    /\[(HOOK|INTRODUCTION|MAIN|KEY INSIGHTS|CONCLUSION)\]/g,
    '<span class="script-section-label">[$1]</span>'
  );

  // Highlight B-Roll cues
  html = html.replace(
    /\[B-Roll: ([^\]]+)\]/g,
    '<span class="broll-cue">[B-Roll: $1]</span>'
  );

  // Highlight on-screen text cues
  html = html.replace(
    /\[TEXT: ([^\]]+)\]/g,
    '<span class="text-cue">[TEXT: $1]</span>'
  );

  // Bold **text**
  html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");

  // Convert line breaks to paragraphs
  html = html
    .split("\n\n")
    .map(para => para.trim())
    .filter(para => para.length > 0)
    .map(para => `<p>${para.replace(/\n/g, "<br/>")}</p>`)
    .join("\n");

  return html;
}
