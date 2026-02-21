// Result Display Component
// Shows the analysis results from backend in a clean card format
export default function ResultDisplay({ data }) {
  const { crime_type, time, summary, predicted_section, special_note } = data;

  return (
    <div className="result-card">
      <h2>Analysis result</h2>
      <div className="result-grid">
        <div>
          <p className="label">Crime type</p>
          <p className="value">{crime_type}</p>
        </div>
        <div>
          <p className="label">Time</p>
          <p className="value">{time}</p>
        </div>
        <div>
          <p className="label">Section</p>
          <p className="value">{predicted_section}</p>
        </div>
      </div>
      <p className="summary">{summary}</p>
      {special_note && (
        <p className="special-note" style={{ marginTop: '1rem', padding: '0.75rem', backgroundColor: '#fff3cd', borderRadius: '8px', fontSize: '0.9rem' }}>
          <strong>Note:</strong> {special_note}
        </p>
      )}
    </div>
  );
}
