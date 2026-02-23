import { useState } from "react";
import ComplaintForm from "./components/ComplaintForm";
import ResultDisplay from "./components/ResultDisplay";

// Main App Component
// Manages state for the entire application and coordinates child components
export default function App() {
  // State: stores analysis result from backend
  const [analysis, setAnalysis] = useState(null);
  // State: tracks submission status (idle, loading, done, error)
  const [status, setStatus] = useState("idle");
  // State: stores error messages
  const [error, setError] = useState("");

  const isLoading = status === "loading";

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
          </div>
        </div>
      ) : null}
    </div>
  );
}
