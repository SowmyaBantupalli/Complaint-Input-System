export default function ResultDisplay({ data }) {
  const { crime_type, time, summary, predicted_section } = data;

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
    </div>
  );
}
