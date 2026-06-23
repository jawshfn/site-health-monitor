import React, { useEffect, useState } from "react";
import "./App.css";

const CHECK_API_URL = "http://127.0.0.1:8000/api/check";
const HISTORY_API_URL = "http://127.0.0.1:8000/api/history?limit=10";

function App() {
  const [url, setUrl] = useState("");
  const [result, setResult] = useState(null);
  const [isChecking, setIsChecking] = useState(false);
  const [message, setMessage] = useState("");
  const [history, setHistory] = useState([]);
  const [isHistoryLoading, setIsHistoryLoading] = useState(false);
  const [historyMessage, setHistoryMessage] = useState("");

  useEffect(() => {
    loadHistory();
  }, []);

  async function loadHistory() {
    setIsHistoryLoading(true);
    setHistoryMessage("");

    try {
      const response = await fetch(HISTORY_API_URL);

      if (!response.ok) {
        throw new Error(`History request failed with status ${response.status}.`);
      }

      const data = await response.json();
      setHistory(data);
    } catch (error) {
      setHistoryMessage(
        "Could not load recent history. Make sure the backend is running at http://127.0.0.1:8000."
      );
    } finally {
      setIsHistoryLoading(false);
    }
  }

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
      const response = await fetch(CHECK_API_URL, {
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
      await loadHistory();
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
        <div>
          <p className="eyebrow">Site Health Monitor</p>
          <h1>Check website availability</h1>
          <p>
            Enter a URL to check response status, response time, redirect target,
            and DNS/IP information from the FastAPI backend.
          </p>
        </div>
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
              aria-describedby="url-help"
            />
            <button type="submit" disabled={isChecking}>
              {isChecking ? "Checking..." : "Check Site"}
            </button>
          </div>
          <p id="url-help" className="field-help">
            Try a domain like example.com or a full URL like https://example.com.
          </p>
        </form>

        {isChecking && <p className="status-message">Checking website...</p>}
        {message && <p className="error-message">{message}</p>}
        {result && <ResultCard result={result} />}
      </section>

      <HistorySection
        history={history}
        isLoading={isHistoryLoading}
        message={historyMessage}
        onRefresh={loadHistory}
      />
    </main>
  );
}

function ResultCard({ result }) {
  return (
    <article className={`result-card ${result.is_up ? "result-up" : "result-down"}`}>
      <div className="result-header">
        <div>
          <p className="section-label">Latest Result</p>
          <h2>{result.hostname ?? result.input_url ?? "Website check"}</h2>
        </div>
        <StatusBadge isUp={result.is_up} />
      </div>

      <div className="result-summary" aria-label="Result summary">
        <SummaryItem label="Status" value={result.is_up ? "Reachable" : "Not reachable"} />
        <SummaryItem label="HTTP" value={result.status_code ?? "Not available"} />
        <SummaryItem
          label="Response"
          value={formatResponseTime(result.response_time_ms) ?? "Not available"}
        />
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

function HistorySection({ history, isLoading, message, onRefresh }) {
  return (
    <section className="history-panel" aria-label="Recent check history">
      <div className="history-header">
        <div>
          <p className="section-label">Recent History</p>
          <h2>Saved Checks</h2>
        </div>
        <button type="button" className="secondary-button" onClick={onRefresh} disabled={isLoading}>
          {isLoading ? "Refreshing..." : "Refresh History"}
        </button>
      </div>

      {isLoading && <p className="status-message">Loading recent checks...</p>}
      {message && <p className="error-message">{message}</p>}
      {!isLoading && !message && history.length === 0 && (
        <p className="empty-message">No saved checks yet.</p>
      )}
      {!message && history.length > 0 && <HistoryTable history={history} />}
    </section>
  );
}

function HistoryTable({ history }) {
  return (
    <div className="history-table-wrap">
      <table className="history-table">
        <thead>
          <tr>
            <th scope="col">Host</th>
            <th scope="col">URL</th>
            <th scope="col">Status</th>
            <th scope="col">HTTP</th>
            <th scope="col">Time</th>
            <th scope="col">Checked</th>
            <th scope="col">Error</th>
          </tr>
        </thead>
        <tbody>
          {history.map((check) => (
            <tr key={check.id}>
              <td data-label="Host">{check.hostname ?? "Not available"}</td>
              <td data-label="URL" className="url-cell">
                {check.normalized_url ?? check.input_url ?? "Not available"}
              </td>
              <td data-label="Status">
                <StatusBadge isUp={check.is_up} />
              </td>
              <td data-label="HTTP">{check.status_code ?? "Not available"}</td>
              <td data-label="Time">{formatResponseTime(check.response_time_ms) ?? "Not available"}</td>
              <td data-label="Checked">{formatDate(check.checked_at) ?? "Not available"}</td>
              <td data-label="Error" className="error-cell">
                {check.error ?? "None"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function StatusBadge({ isUp }) {
  return (
    <span className={isUp ? "badge badge-up" : "badge badge-down"}>
      <span aria-hidden="true">{isUp ? "OK" : "!"}</span>
      {isUp ? "Up" : "Down"}
    </span>
  );
}

function SummaryItem({ label, value }) {
  return (
    <div className="summary-item">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
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
