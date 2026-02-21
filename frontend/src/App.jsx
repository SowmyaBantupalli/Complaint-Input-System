import { useState } from "react";
import ComplaintForm from "./components/ComplaintForm";
import ResultDisplay from "./components/ResultDisplay";

export default function App() {
  const [analysis, setAnalysis] = useState(null);
  const [status, setStatus] = useState("idle");
  const [error, setError] = useState("");

  return (
    <div className="app-shell">
      <header>
        <p className="eyebrow">College Demo</p>
        <h1>Complaint Analyzer</h1>
        <p>Tell us what happened and get a quick crime summary.</p>
      </header>

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

      {status === "loading" && <p className="status">Sending complaint…</p>}
      {error && <p className="status status-error">{error}</p>}
      {analysis && <ResultDisplay data={analysis} />}
    </div>
  );
}
