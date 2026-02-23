import { useEffect, useMemo, useState } from "react";
import ComplaintForm from "./components/ComplaintForm";
import ResultDisplay from "./components/ResultDisplay";
import { BNS_INFO_CARDS } from "./bns_info";

// Main App Component
// Manages state for the entire application and coordinates child components
export default function App() {
  // State: stores analysis result from backend
  const [analysis, setAnalysis] = useState(null);
  // State: tracks submission status (idle, loading, done, error)
  const [status, setStatus] = useState("idle");
  // State: stores error messages
  const [error, setError] = useState("");
  const [bnsCardIndex, setBnsCardIndex] = useState(0);

  const isLoading = status === "loading";

  const activeBnsCard = useMemo(() => {
    if (!BNS_INFO_CARDS.length) return null;
    const safeIndex = ((bnsCardIndex % BNS_INFO_CARDS.length) + BNS_INFO_CARDS.length) % BNS_INFO_CARDS.length;
    return BNS_INFO_CARDS[safeIndex];
  }, [bnsCardIndex]);

  useEffect(() => {
    if (!isLoading) return;
    // Rotate informational content while loading.
    const id = window.setInterval(() => {
      setBnsCardIndex((x) => x + 1);
    }, 5500);
    return () => window.clearInterval(id);
  }, [isLoading]);

  return (
    <div className={isLoading ? "app-shell app-shell-loading" : "app-shell"}>
      <div className="app-content">
        <header>
          <div className="eyebrow">Complaint Intake</div>
          <h1>AI Complaint Analysis</h1>
          <p>Complaint analysis with BNS section identification.</p>
        </header>

        {/* Complaint input form - handles user input and API calls */}
        <ComplaintForm
          isLoading={isLoading}
          onStart={() => {
            setAnalysis(null);
            setStatus("loading");
            setError("");
            setBnsCardIndex(0);
          }}
          onResult={(result) => {
            setAnalysis(result);
            setStatus("done");
          }}
          onError={(message) => {
            setError(message);
            setStatus("error");
          }}
        />

        {/* Conditional rendering based on status */}
        {error && <p className="status status-error">{error}</p>}
        {analysis && <ResultDisplay data={analysis} />}
      </div>

      {isLoading ? (
        <div className="loading-overlay" role="status" aria-live="polite" aria-busy="true">
          <div className="loading-card">
            <div className="ai-loader" aria-hidden="true" />
            <h2>Analyzing with AI</h2>
            <p>The system is structuring the complaint and identifying relevant BNS sections. Please wait.</p>

            {activeBnsCard ? (
              <div className="loading-info" aria-label="Information about Bharatiya Nyaya Sanhita">
                <div className="loading-info-title">About Bharatiya Nyaya Sanhita (BNS)</div>
                <button
                  type="button"
                  className="loading-info-card"
                  key={activeBnsCard.title}
                  aria-label="Next BNS information card"
                  onClick={() => setBnsCardIndex((x) => x + 1)}
                >
                  <div className="loading-info-card-title">{activeBnsCard.title}</div>
                  <div className="loading-info-card-body">{activeBnsCard.body}</div>
                </button>
              </div>
            ) : null}
          </div>
        </div>
      ) : null}
    </div>
  );
}
