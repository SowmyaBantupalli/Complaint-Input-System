// Result Display Component
// Shows the analysis results from backend in a clean card format
import { useState } from "react";

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
    bns_sections,
    ai_powered,
    extracted_text,
    consistency,
  } = data;

  const [openTooltipSection, setOpenTooltipSection] = useState(null);

  const renderValue = (value) => {
    const raw = String(value ?? "").trim();
    if (!raw) return <span className="value value-muted">Not available</span>;

    const parts = raw
      .split(",")
      .map((p) => p.trim())
      .filter(Boolean);

    if (parts.length >= 2) {
      return (
        <ul className="value-list">
          {parts.map((p) => (
            <li key={p}>{p}</li>
          ))}
        </ul>
      );
    }

    return <span className="value">{raw}</span>;
  };

  const normalizedSections = Array.isArray(bns_sections)
    ? bns_sections
        .map((s) => {
          if (!s) return null;
          if (typeof s === "string") return { section: s, reason: "" };
          return {
            section: String(s.section ?? "").trim(),
            reason: String(s.reason ?? "").trim(),
            description: String(s.description ?? "").trim(),
            name: String(s.name ?? "").trim(),
            chapter: String(s.chapter ?? "").trim(),
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
        {consistency?.typed_provided && consistency?.image_provided && consistency?.matched === true ? (
          <span className="pill pill-success">Inputs verified</span>
        ) : null}
        {severity ? <span className="pill pill-accent">Severity: {severity}</span> : null}
      </div>

      <div className="result-list">
        <div className="result-item">
          <div className="label">Crime Type</div>
          <div className="value-block">{renderValue(crime_type)}</div>
        </div>
        <div className="result-item">
          <div className="label">Location</div>
          <div className="value-block">{renderValue(location)}</div>
        </div>
        <div className="result-item">
          <div className="label">Date</div>
          <div className="value-block">{renderValue(date)}</div>
        </div>
        <div className="result-item">
          <div className="label">Time</div>
          <div className="value-block">{renderValue(time)}</div>
        </div>
        <div className="result-item">
          <div className="label">Persons Involved</div>
          <div className="value-block">{renderValue(persons_involved)}</div>
        </div>
      </div>

      <div className="key-event">
        <p className="label">Key Event Summary</p>
        <p className="event-text">{key_event_summary || "Not available"}</p>
      </div>

      <div className="sections">
        <p className="label">BNS Sections</p>
        {normalizedSections.length > 0 ? (
          <ul className="section-list">
            {normalizedSections.map((s) => (
              <li key={s.section} className="section-item">
                <div className="section-head">
                  <span className="section-id">Section {s.section}</span>
                  {s.description ? (
                    <div className={openTooltipSection === s.section ? "section-tooltip is-open" : "section-tooltip"}>
                      <button
                        type="button"
                        className="info-button"
                        aria-label={`View description for Section ${s.section}`}
                        aria-expanded={openTooltipSection === s.section}
                        aria-controls={`section-desc-${s.section}`}
                        onClick={() => {
                          setOpenTooltipSection((prev) => (prev === s.section ? null : s.section));
                        }}
                      >
                        <span className="info-dot" aria-hidden="true">i</span>
                      </button>
                      <div className="tooltip-body" id={`section-desc-${s.section}`} role="note">
                        <div className="tooltip-title">Official Description</div>
                        <div className="tooltip-text">{s.description}</div>
                      </div>
                    </div>
                  ) : null}
                </div>
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
    </div>
  );
}
