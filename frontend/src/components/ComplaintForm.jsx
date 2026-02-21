import { useState } from "react";

export default function ComplaintForm({ onStart, onResult, onError }) {
  const [complaint, setComplaint] = useState("");
  const [file, setFile] = useState(null);

  const buildFormData = () => {
    const formData = new FormData();
    if (complaint) {
      formData.append("complaint", complaint);
    }
    if (file) {
      formData.append("image", file);
    }
    return formData;
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!complaint && !file) {
      onError("Write a complaint or upload an image before submitting.");
      return;
    }

    onStart();

    try {
      const response = await fetch("http://localhost:8000/analyze", {
        method: "POST",
        body: buildFormData(),
      });

      const payload = await response.json();

      if (!response.ok) {
        throw new Error(payload.detail || "Unable to analyze right now.");
      }

      onResult(payload);
    } catch (err) {
      onError(err.message);
    }
  };

  return (
    <form className="form-card" onSubmit={handleSubmit}>
      <label>
        Complaint story
        <textarea
          value={complaint}
          onChange={(event) => setComplaint(event.target.value)}
          placeholder="Describe what happened"
          rows={5}
        />
      </label>

      <label className="file-input">
        Optional image
        <input
          type="file"
          accept="image/*"
          onChange={(event) => setFile(event.target.files?.[0] ?? null)}
        />
      </label>

      <button type="submit">Analyze complaint</button>
    </form>
  );
}
