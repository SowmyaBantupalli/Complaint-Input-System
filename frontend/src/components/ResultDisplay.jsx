// Result Display Component
// Shows the analysis results from backend in a clean card format
export default function ResultDisplay({ data }) {
  const {
    crime_type,
    location,
    date,
    time,
    persons_involved,
    key_event_summary,
    predicted_section,
    severity,
    additional_notes,
    bns_sections,
    ai_powered,
    extracted_text,
  } = data;

  const normalizedSections = Array.isArray(bns_sections)
    ? bns_sections
        .map((s) => {
          if (!s) return null;
          if (typeof s === "string") return { section: s, reason: "" };
          return {
            section: String(s.section ?? "").trim(),
            reason: String(s.reason ?? "").trim(),
          };
        })
        .filter((s) => s && s.section)
    : [];

  return (
    <div className="result-card">
      <h2>Analysis Result</h2>

      <div className="result-meta">
        <span className={ai_powered ? "pill pill-success" : "pill pill-muted"}>
          {ai_powered ? "AI-assisted" : "Standard"}
        </span>
        {severity ? <span className="pill pill-accent">Severity: {severity}</span> : null}
      </div>

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
          <p className="label">Date</p>
          <p className="value">{date}</p>
        </div>
        <div>
          <p className="label">Time</p>
          <p className="value">{time}</p>
        </div>
        <div>
          <p className="label">Persons Involved</p>
          <p className="value">{persons_involved}</p>
        </div>
      </div>

      <div className="key-event">
        <p className="label">Key Event Summary</p>
        <p className="event-text">{key_event_summary || "Not available"}</p>
      </div>

      <div className="sections">
        <p className="label">BNS Sections (Official CSV)</p>
        {normalizedSections.length > 0 ? (
          <ul className="section-list">
            {normalizedSections.map((s) => (
              <li key={s.section}>
                <span className="section-id">Section {s.section}</span>
                {s.reason ? <span className="section-reason">{s.reason}</span> : null}
              </li>
            ))}
          </ul>
        ) : (
          <p className="value value-muted">{predicted_section || "Section not determined"}</p>
        )}
      </div>

      {extracted_text ? (
        <div className="summary">
          <span className="summary-title">Extracted Text (From Image)</span>
          <div className="summary-body">{extracted_text}</div>
        </div>
      ) : null}

      {additional_notes ? (
        <div className="special-note">
          <strong>Notes:</strong> {additional_notes}
        </div>
      ) : null}
    </div>
  );
}
