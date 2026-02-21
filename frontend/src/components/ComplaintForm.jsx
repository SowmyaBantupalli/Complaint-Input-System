import { useState } from "react";

// MODULE 1: Complaint Input Form Component
// Handles user input (text or image) and sends to backend API
export default function ComplaintForm({ onStart, onResult, onError }) {
  // State management for form inputs
  const [complaint, setComplaint] = useState("");
  const [file, setFile] = useState(null);

  // Build multipart/form-data for backend submission
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

  // Form submission handler - calls backend API
  const handleSubmit = async (event) => {
    event.preventDefault();
    
    // Validation: ensure at least one input is provided
    if (!complaint && !file) {
      onError("Write a complaint or upload an image before submitting.");
      return;
    }

    onStart();  // Notify parent component that submission started

    // Get backend URL from environment variable or use localhost for dev
    const backendUrl = import.meta.env.VITE_BACKEND_URL || "http://localhost:8000";

    try {
      // Send POST request with FormData to backend /analyze endpoint
      const response = await fetch(`${backendUrl}/analyze`, {
        method: "POST",
        body: buildFormData(),
      });

      // Parse JSON response
      const payload = await response.json();

      // Check for errors
      if (!response.ok) {
        throw new Error(payload.detail || "Unable to analyze right now.");
      }

      // Success: pass result to parent component
      onResult(payload);
    } catch (err) {
      // Handle errors (network issues, backend errors, etc.)
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
