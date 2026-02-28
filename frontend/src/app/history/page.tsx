"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

const API = "http://localhost:8000/api";

interface HistoryItem {
    id: string;
    created_at: string;
    prompt: string;
    category: string;
    num_results: number;
    total_scraped: number;
}

export default function HistoryPage() {
    const [history, setHistory] = useState<HistoryItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        fetch(`${API}/history`)
            .then((res) => {
                if (!res.ok) throw new Error("Failed to load history");
                return res.json();
            })
            .then((data) => setHistory(data.history || []))
            .catch((err) => setError(err.message))
            .finally(() => setLoading(false));
    }, []);

    const formatDate = (iso: string) => {
        try {
            return new Date(iso).toLocaleDateString("en-US", {
                month: "short",
                day: "numeric",
                year: "numeric",
                hour: "2-digit",
                minute: "2-digit",
            });
        } catch {
            return iso;
        }
    };

    return (
        <>
            <div className="page-header">
                <h2>📁 Research History</h2>
                <p>View all past research runs and their generated reports</p>
            </div>

            <div className="card">
                {loading && (
                    <div className="run-status">
                        <div className="spinner" />
                        <div className="status-text">Loading history...</div>
                    </div>
                )}

                {error && (
                    <div className="error-box">
                        <strong>Error:</strong> {error}
                    </div>
                )}

                {!loading && !error && history.length === 0 && (
                    <div className="empty-state">
                        <div className="empty-icon">📭</div>
                        <h3>No research runs yet</h3>
                        <p>Run your first research from the <Link href="/" style={{ color: "var(--accent-blue)" }}>Dashboard</Link> to see it here.</p>
                    </div>
                )}

                {!loading && !error && history.length > 0 && (
                    <table className="history-table">
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>Prompt</th>
                                <th>Category</th>
                                <th>Results</th>
                                <th>Scraped</th>
                            </tr>
                        </thead>
                        <tbody>
                            {history.map((item) => (
                                <tr key={item.id} onClick={() => window.location.href = `/history/${item.id}`}>
                                    <td style={{ whiteSpace: "nowrap" }}>{formatDate(item.created_at)}</td>
                                    <td style={{ maxWidth: 300, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                                        {item.prompt}
                                    </td>
                                    <td>
                                        <span className="badge badge-violet">{item.category || "General"}</span>
                                    </td>
                                    <td>
                                        <span className="badge badge-blue">{item.num_results}</span>
                                    </td>
                                    <td>
                                        <span className="badge badge-emerald">{item.total_scraped}</span>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>
        </>
    );
}
