"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

const API = "http://localhost:8000/api";

interface ResearchRecord {
    id: string;
    created_at: string;
    inputs: {
        prompt: string;
        target_urls: string[];
        time_window: string;
        category: string;
        num_results: number;
    };
    report_markdown: string;
    selected_results: unknown[];
    total_scraped: number;
}

export default function HistoryDetailPage() {
    const params = useParams();
    const id = params.id as string;
    const [record, setRecord] = useState<ResearchRecord | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [toast, setToast] = useState<{ message: string; type: string } | null>(null);

    const showToast = (message: string, type: string = "success") => {
        setToast({ message, type });
        setTimeout(() => setToast(null), 3000);
    };

    useEffect(() => {
        fetch(`${API}/history/${id}`)
            .then((res) => {
                if (!res.ok) throw new Error("Research record not found");
                return res.json();
            })
            .then((data) => setRecord(data))
            .catch((err) => setError(err.message))
            .finally(() => setLoading(false));
    }, [id]);

    const formatDate = (iso: string) => {
        try {
            return new Date(iso).toLocaleDateString("en-US", {
                month: "long",
                day: "numeric",
                year: "numeric",
                hour: "2-digit",
                minute: "2-digit",
            });
        } catch {
            return iso;
        }
    };

    const copyMarkdown = () => {
        if (record?.report_markdown) {
            navigator.clipboard.writeText(record.report_markdown);
            showToast("Markdown copied to clipboard!");
        }
    };

    const downloadMarkdown = () => {
        if (record?.report_markdown) {
            const blob = new Blob([record.report_markdown], { type: "text/markdown" });
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `research-${record.id.slice(0, 8)}.md`;
            a.click();
            URL.revokeObjectURL(url);
            showToast("Downloaded!");
        }
    };

    if (loading) {
        return (
            <div className="card">
                <div className="run-status">
                    <div className="spinner" />
                    <div className="status-text">Loading research record...</div>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <>
                <Link href="/history" className="back-link">← Back to History</Link>
                <div className="error-box"><strong>Error:</strong> {error}</div>
            </>
        );
    }

    if (!record) return null;

    return (
        <>
            <Link href="/history" className="back-link">← Back to History</Link>

            <div className="page-header">
                <h2>📄 Research Report</h2>
                <p>{record.inputs.prompt}</p>
            </div>

            <div className="detail-meta">
                <div className="meta-item">
                    <span className="meta-label">Date</span>
                    <span className="meta-value">{formatDate(record.created_at)}</span>
                </div>
                <div className="meta-item">
                    <span className="meta-label">Time Window</span>
                    <span className="meta-value">{record.inputs.time_window}</span>
                </div>
                <div className="meta-item">
                    <span className="meta-label">Category</span>
                    <span className="meta-value">{record.inputs.category || "General"}</span>
                </div>
                <div className="meta-item">
                    <span className="meta-label">Results</span>
                    <span className="meta-value">{record.selected_results?.length || 0}</span>
                </div>
                <div className="meta-item">
                    <span className="meta-label">Total Scraped</span>
                    <span className="meta-value">{record.total_scraped}</span>
                </div>
                <div className="meta-item">
                    <span className="meta-label">Record ID</span>
                    <span className="meta-value" style={{ fontFamily: "monospace", fontSize: 12 }}>{record.id}</span>
                </div>
            </div>

            <div className="markdown-viewer">
                <div className="markdown-actions">
                    <button className="btn btn-secondary btn-sm" onClick={copyMarkdown}>📋 Copy Markdown</button>
                    <button className="btn btn-secondary btn-sm" onClick={downloadMarkdown}>⬇️ Download .md</button>
                </div>
                <div
                    className="markdown-content"
                    dangerouslySetInnerHTML={{ __html: renderMarkdown(record.report_markdown) }}
                />
            </div>

            {toast && <div className={`toast toast-${toast.type}`}>{toast.message}</div>}
        </>
    );
}

/** Simple markdown-to-HTML renderer */
function renderMarkdown(md: string): string {
    let html = md
        .replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>')
        .replace(/^### (.+)$/gm, '<h3>$1</h3>')
        .replace(/^## (.+)$/gm, '<h2>$1</h2>')
        .replace(/^# (.+)$/gm, '<h1>$1</h1>')
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.+?)\*/g, '<em>$1</em>')
        .replace(/`(.+?)`/g, '<code>$1</code>')
        .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')
        .replace(/^---$/gm, '<hr/>')
        .replace(/^- (.+)$/gm, '<li>$1</li>')
        .replace(/^\d+\. (.+)$/gm, '<li>$1</li>')
        .replace(/^\|(.+)\|$/gm, (match: string) => {
            const cells = match.split('|').filter(c => c.trim());
            if (cells.every(c => /^[\s-:]+$/.test(c))) return '';
            return '<tr>' + cells.map(c => `<td>${c.trim()}</td>`).join('') + '</tr>';
        })
        .replace(/^> (.+)$/gm, '<blockquote>$1</blockquote>')
        .replace(/^(?!<[a-z])((?!^\s*$).+)$/gm, '<p>$1</p>');

    html = html.replace(/(<li>[\s\S]*?<\/li>)/g, '<ul>$1</ul>');
    html = html.replace(/<\/ul>\s*<ul>/g, '');
    html = html.replace(/(<tr>[\s\S]*?<\/tr>)/g, '<table>$1</table>');
    html = html.replace(/<\/table>\s*<table>/g, '');

    return html;
}
