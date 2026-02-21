// Result Display Component
// Shows the analysis results from backend in a clean card format
export default function ResultDisplay({ data }) {
  const { crime_type, location, time, persons_involved, key_event, summary, predicted_section, special_note } = data;

  return (
    <div className="result-card">
      <h2>Analysis Result</h2>
      <div className="result-grid">
        <div>
          <p className="label">Crime Type</p>
          <p className="value">{crime_type}</p>
        </div>
        <div>
          <p className="label">Location</p>
          <p className="value">{location}</p>
        </div>
        <div>
          <p className="label">Time</p>
          <p className="value">{time}</p>
        </div>
        <div>
          <p className="label">Persons Involved</p>
          <p className="value">{persons_involved}</p>
        </div>
        <div>
          <p className="label">Legal Section</p>
          <p className="value">{predicted_section}</p>
        </div>
      </div>
      <div className="key-event">
        <p className="label">Key Event</p>
        <p className="event-text">{key_event}</p>
      </div>
      <div className="summary">{summary}</div>
      {special_note && (
        <div className="special-note">
          <strong>Special Note:</strong> {special_note}
        </div>
      )}
    </div>
  );
}
