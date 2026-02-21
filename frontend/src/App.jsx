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

  return (
    <div className="app-shell">
      <header>
        <h1>Complaint Analyzer</h1>
        <p>Tell us what happened and get a quick crime summary.</p>
      </header>

      {/* Complaint input form - handles user input and API calls */}
      <ComplaintForm
        onStart={() => {
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
      {status === "loading" && <p className="status">Sending complaint…</p>}
      {error && <p className="status status-error">{error}</p>}
      {analysis && <ResultDisplay data={analysis} />}
    </div>
  );
}
