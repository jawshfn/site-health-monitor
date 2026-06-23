import React, { useState } from "react";
import "./App.css";

const API_URL = "http://127.0.0.1:8000/api/check";

function App() {
  const [url, setUrl] = useState("");
  const [result, setResult] = useState(null);
  const [isChecking, setIsChecking] = useState(false);
  const [message, setMessage] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();

    const trimmedUrl = url.trim();
    if (!trimmedUrl) {
      setMessage("Enter a website URL before checking.");
      setResult(null);
      return;
    }

    setIsChecking(true);
    setMessage("");
    setResult(null);

    try {
      const response = await fetch(API_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ url: trimmedUrl }),
      });

      if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}.`);
      }

      const data = await response.json();
      setResult(data);
    } catch (error) {
      setMessage(
        "Could not check the site. Make sure the backend is running at http://127.0.0.1:8000."
      );
    } finally {
      setIsChecking(false);
    }
  }

  return (
    <main className="app-shell">
      <section className="intro">
        <p className="eyebrow">Site Health Monitor</p>
        <h1>Check website availability</h1>
        <p>
          Enter a URL to check response status, response time, redirect target,
          and DNS/IP information from the FastAPI backend.
        </p>
      </section>

      <section className="checker-panel" aria-label="Website checker">
        <form onSubmit={handleSubmit} className="check-form">
          <label htmlFor="url">Website URL</label>
          <div className="form-row">
            <input
              id="url"
              type="text"
              value={url}
              onChange={(event) => setUrl(event.target.value)}
              placeholder="example.com"
              disabled={isChecking}
            />
            <button type="submit" disabled={isChecking}>
              {isChecking ? "Checking..." : "Check Site"}
            </button>
          </div>
        </form>

        {isChecking && <p className="status-message">Checking website...</p>}
        {message && <p className="error-message">{message}</p>}
        {result && <ResultCard result={result} />}
      </section>
    </main>
  );
}

function ResultCard({ result }) {
  return (
    <article className="result-card">
      <div className="result-header">
        <h2>Check Result</h2>
        <span className={result.is_up ? "badge badge-up" : "badge badge-down"}>
          {result.is_up ? "Up" : "Down"}
        </span>
      </div>

      <dl className="result-grid">
        <ResultRow label="Input URL" value={result.input_url} />
        <ResultRow label="Normalized URL" value={result.normalized_url} />
        <ResultRow label="Final URL" value={result.final_url} />
        <ResultRow label="Hostname" value={result.hostname} />
        <ResultRow label="Status Code" value={result.status_code} />
        <ResultRow label="Response Time" value={formatResponseTime(result.response_time_ms)} />
        <ResultRow label="IP Addresses" value={formatIpAddresses(result.ip_addresses)} />
        <ResultRow label="Checked At" value={formatDate(result.checked_at)} />
        {result.error && <ResultRow label="Error" value={result.error} />}
      </dl>
    </article>
  );
}

function ResultRow({ label, value }) {
  return (
    <div className="result-row">
      <dt>{label}</dt>
      <dd>{value ?? "Not available"}</dd>
    </div>
  );
}

function formatResponseTime(value) {
  if (value === null || value === undefined) {
    return null;
  }

  return `${value} ms`;
}

function formatIpAddresses(value) {
  if (!value || value.length === 0) {
    return null;
  }

  return value.join(", ");
}

function formatDate(value) {
  if (!value) {
    return null;
  }

  return new Date(value).toLocaleString();
}

export default App;
