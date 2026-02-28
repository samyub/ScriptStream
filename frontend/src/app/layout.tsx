import type { Metadata } from "next";
import "./globals.css";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Dyut — YouTube Research Agent",
  description: "PRAT Framework research dashboard for YouTube content creators",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <div className="app-layout">
          <aside className="sidebar">
            <div className="sidebar-logo">
              <div className="logo-icon">🔬</div>
              <div>
                <h1>Dyut</h1>
                <span className="subtitle">Research Agent</span>
              </div>
            </div>
            <nav className="sidebar-nav">
              <Link href="/" className="nav-link" id="nav-dashboard">
                <span className="nav-icon">📊</span>
                Dashboard
              </Link>
              <Link href="/history" className="nav-link" id="nav-history">
                <span className="nav-icon">📁</span>
                History
              </Link>
            </nav>
          </aside>
          <main className="main-content">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
