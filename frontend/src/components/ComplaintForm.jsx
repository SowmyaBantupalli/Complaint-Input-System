import { useRef, useState } from "react";

// MODULE 1: Complaint Input Form Component
// Handles user input (text or image) and sends to backend API
export default function ComplaintForm({ onStart, onResult, onError, isLoading = false }) {
  // State management for form inputs
  const [complaint, setComplaint] = useState("");
  const [file, setFile] = useState(null);
  const fileInputRef = useRef(null);

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
      onError("Please enter the complaint details or upload an image of Written complaint.");
      return;
    }

    onStart();  // Notify parent component that submission started

    // Get backend URL from environment variable or use localhost for dev
    // Remove trailing slash to prevent double slashes in the endpoint URL
    const backendUrl = (import.meta.env.VITE_BACKEND_URL || "http://localhost:8000").replace(/\/$/, "");

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
        throw new Error(payload.detail || "Unable to process the request at this time.");
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
        Complaint Details
        <textarea
          value={complaint}
          onChange={(event) => setComplaint(event.target.value)}
          placeholder="Provide a clear description of the incident (who, what, where, and when)."
          rows={7}
          disabled={isLoading}
        />
      </label>

      <p className="form-hint">
        If both typed details and an image are provided, the system will verify that they refer to the same complaint.
      </p>

      <label className="file-input">
        Supporting Document (Image)
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={(event) => setFile(event.target.files?.[0] ?? null)}
          disabled={isLoading}
        />
      </label>

      {file ? (
        <div className="file-actions" aria-live="polite">
          <div className="file-name">Selected file: {file.name}</div>
          <button
            type="button"
            className="button-secondary"
            onClick={() => {
              setFile(null);
              if (fileInputRef.current) {
                fileInputRef.current.value = "";
              }
            }}
            disabled={isLoading}
          >
            Clear Image
          </button>
        </div>
      ) : null}

      <button type="submit" disabled={isLoading}>
        {isLoading ? "Analyzing with AI..." : "Submit for Analysis"}
      </button>
    </form>
  );
}
