import React, { useEffect, useState } from "react";
import "./App.css";

const CHECK_API_URL = "http://127.0.0.1:8000/api/check";
const HISTORY_API_URL = "http://127.0.0.1:8000/api/history";
const HISTORY_PAGE_SIZE = 10;
const CLEAR_HISTORY_API_URL = "http://127.0.0.1:8000/api/history";
const SITES_API_URL = "http://127.0.0.1:8000/api/sites";
const CHECK_ALL_API_URL = "http://127.0.0.1:8000/api/sites/check-all";

function App() {
  const [url, setUrl] = useState("");
  const [result, setResult] = useState(null);
  const [isChecking, setIsChecking] = useState(false);
  const [message, setMessage] = useState("");
  const [siteUrl, setSiteUrl] = useState("");
  const [siteName, setSiteName] = useState("");
  const [savedSites, setSavedSites] = useState([]);
  const [isSitesLoading, setIsSitesLoading] = useState(false);
  const [isSavingSite, setIsSavingSite] = useState(false);
  const [checkingSiteId, setCheckingSiteId] = useState(null);
  const [deletingSiteId, setDeletingSiteId] = useState(null);
  const [isCheckingAllSites, setIsCheckingAllSites] = useState(false);
  const [checkAllResult, setCheckAllResult] = useState(null);
  const [checkAllMessage, setCheckAllMessage] = useState("");
  const [sitesMessage, setSitesMessage] = useState("");
  const [history, setHistory] = useState([]);
  const [historyTotal, setHistoryTotal] = useState(0);
  const [hasMoreHistory, setHasMoreHistory] = useState(false);
  const [isHistoryLoading, setIsHistoryLoading] = useState(false);
  const [isLoadingMoreHistory, setIsLoadingMoreHistory] = useState(false);
  const [isClearingHistory, setIsClearingHistory] = useState(false);
  const [historyMessage, setHistoryMessage] = useState("");
  const [historyNotice, setHistoryNotice] = useState("");

  useEffect(() => {
    loadHistory();
    loadSavedSites();
  }, []);

  async function loadHistory({ offset = 0, append = false } = {}) {
    if (append) {
      setIsLoadingMoreHistory(true);
    } else {
      setIsHistoryLoading(true);
    }
    setHistoryMessage("");
    setHistoryNotice("");

    try {
      const response = await fetch(
        `${HISTORY_API_URL}?limit=${HISTORY_PAGE_SIZE}&offset=${offset}`
      );

      if (!response.ok) {
        throw new Error(`History request failed with status ${response.status}.`);
      }

      const data = await response.json();
      setHistory((currentHistory) => (append ? [...currentHistory, ...data.items] : data.items));
      setHistoryTotal(data.total);
      setHasMoreHistory(data.has_more);
    } catch (error) {
      setHistoryMessage(
        "Could not load recent history. Make sure the backend is running at http://127.0.0.1:8000."
      );
    } finally {
      setIsHistoryLoading(false);
      setIsLoadingMoreHistory(false);
    }
  }

  async function clearHistory() {
    const confirmed = window.confirm(
      "Clear all saved check history? Your saved monitored sites will not be deleted."
    );

    if (!confirmed) {
      return;
    }

    setIsClearingHistory(true);
    setHistoryMessage("");
    setHistoryNotice("");

    try {
      const response = await fetch(CLEAR_HISTORY_API_URL, {
        method: "DELETE",
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.detail ?? `Clear history failed with status ${response.status}.`);
      }

      const data = await response.json();
      setHistory([]);
      setHistoryTotal(0);
      setHasMoreHistory(false);
      setHistoryNotice(`Cleared ${data.deleted_count} saved check results.`);
    } catch (error) {
      setHistoryMessage(
        error instanceof Error
          ? error.message
          : "Could not clear history. Make sure the backend is running."
      );
    } finally {
      setIsClearingHistory(false);
    }
  }

  async function loadSavedSites() {
    setIsSitesLoading(true);
    setSitesMessage("");

    try {
      const response = await fetch(SITES_API_URL);

      if (!response.ok) {
        throw new Error(`Saved sites request failed with status ${response.status}.`);
      }

      const data = await response.json();
      setSavedSites(data);
    } catch (error) {
      setSitesMessage(
        "Could not load saved sites. Make sure the backend is running at http://127.0.0.1:8000."
      );
    } finally {
      setIsSitesLoading(false);
    }
  }

  async function saveSite(event) {
    event.preventDefault();

    const trimmedUrl = siteUrl.trim();
    const trimmedName = siteName.trim();

    if (!trimmedUrl) {
      setSitesMessage("Enter a website URL before saving a site.");
      return;
    }

    setIsSavingSite(true);
    setSitesMessage("");

    try {
      const response = await fetch(SITES_API_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          url: trimmedUrl,
          name: trimmedName || null,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.detail ?? `Save failed with status ${response.status}.`);
      }

      setSiteUrl("");
      setSiteName("");
      await loadSavedSites();
    } catch (error) {
      setSitesMessage(
        error instanceof Error
          ? error.message
          : "Could not save the site. Make sure the backend is running."
      );
    } finally {
      setIsSavingSite(false);
    }
  }

  async function checkSavedSite(site) {
    setCheckingSiteId(site.id);
    setMessage("");
    setResult(null);

    try {
      const data = await checkUrl(site.normalized_url);
      setResult(data);
      await loadHistory();
    } catch (error) {
      setMessage(
        "Could not check the saved site. Make sure the backend is running at http://127.0.0.1:8000."
      );
    } finally {
      setCheckingSiteId(null);
    }
  }

  async function deleteSavedSite(siteId) {
    setDeletingSiteId(siteId);
    setSitesMessage("");

    try {
      const response = await fetch(`${SITES_API_URL}/${siteId}`, {
        method: "DELETE",
      });

      if (!response.ok) {
        throw new Error(`Delete failed with status ${response.status}.`);
      }

      setSavedSites((currentSites) => currentSites.filter((site) => site.id !== siteId));
    } catch (error) {
      setSitesMessage(
        "Could not delete the saved site. Make sure the backend is running at http://127.0.0.1:8000."
      );
    } finally {
      setDeletingSiteId(null);
    }
  }

  async function checkAllSavedSites() {
    if (savedSites.length === 0) {
      setCheckAllMessage("Save at least one site before running Check All.");
      setCheckAllResult(null);
      return;
    }

    setIsCheckingAllSites(true);
    setCheckAllMessage("");
    setCheckAllResult(null);

    try {
      const response = await fetch(CHECK_ALL_API_URL, {
        method: "POST",
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.detail ?? `Check all failed with status ${response.status}.`);
      }

      const data = await response.json();
      setCheckAllResult(data);
      await loadHistory();
    } catch (error) {
      setCheckAllMessage(
        error instanceof Error
          ? error.message
          : "Could not check saved sites. Make sure the backend is running."
      );
    } finally {
      setIsCheckingAllSites(false);
    }
  }

  async function checkUrl(urlToCheck) {
    const response = await fetch(CHECK_API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ url: urlToCheck }),
    });

    if (!response.ok) {
      throw new Error(`Request failed with status ${response.status}.`);
    }

    return response.json();
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
      const data = await checkUrl(trimmedUrl);
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

      <SavedSitesSection
        siteUrl={siteUrl}
        siteName={siteName}
        sites={savedSites}
        isLoading={isSitesLoading}
        isSaving={isSavingSite}
        checkingSiteId={checkingSiteId}
        deletingSiteId={deletingSiteId}
        isCheckingAll={isCheckingAllSites}
        checkAllResult={checkAllResult}
        checkAllMessage={checkAllMessage}
        message={sitesMessage}
        onSiteUrlChange={setSiteUrl}
        onSiteNameChange={setSiteName}
        onSave={saveSite}
        onRefresh={loadSavedSites}
        onCheck={checkSavedSite}
        onCheckAll={checkAllSavedSites}
        onDelete={deleteSavedSite}
      />

      <HistorySection
        history={history}
        total={historyTotal}
        hasMore={hasMoreHistory}
        isLoading={isHistoryLoading}
        isLoadingMore={isLoadingMoreHistory}
        isClearing={isClearingHistory}
        message={historyMessage}
        notice={historyNotice}
        onRefresh={loadHistory}
        onLoadMore={() => loadHistory({ offset: history.length, append: true })}
        onClear={clearHistory}
      />
    </main>
  );
}

function SavedSitesSection({
  siteUrl,
  siteName,
  sites,
  isLoading,
  isSaving,
  checkingSiteId,
  deletingSiteId,
  isCheckingAll,
  checkAllResult,
  checkAllMessage,
  message,
  onSiteUrlChange,
  onSiteNameChange,
  onSave,
  onRefresh,
  onCheck,
  onCheckAll,
  onDelete,
}) {
  return (
    <section className="sites-panel" aria-label="Saved monitored sites">
      <div className="history-header">
        <div>
          <p className="section-label">Watchlist</p>
          <h2>Saved Sites</h2>
        </div>
        <button type="button" className="secondary-button" onClick={onRefresh} disabled={isLoading}>
          {isLoading ? "Refreshing..." : "Refresh Sites"}
        </button>
      </div>

      <form onSubmit={onSave} className="saved-site-form">
        <div className="site-form-field">
          <label htmlFor="site-url">Site URL</label>
          <input
            id="site-url"
            type="text"
            value={siteUrl}
            onChange={(event) => onSiteUrlChange(event.target.value)}
            placeholder="example.com"
            disabled={isSaving}
          />
        </div>
        <div className="site-form-field">
          <label htmlFor="site-name">Friendly name</label>
          <input
            id="site-name"
            type="text"
            value={siteName}
            onChange={(event) => onSiteNameChange(event.target.value)}
            placeholder="Example"
            disabled={isSaving}
          />
        </div>
        <button type="submit" disabled={isSaving}>
          {isSaving ? "Saving..." : "Save Site"}
        </button>
      </form>

      {isLoading && <p className="status-message">Loading saved sites...</p>}
      {message && <p className="error-message">{message}</p>}
      {!isLoading && !message && sites.length === 0 && (
        <p className="empty-message">No saved sites yet.</p>
      )}
      {sites.length > 0 && (
        <>
          <div className="check-all-bar">
            <div>
              <h3>Run all saved checks</h3>
              <p>Check every saved site and add the results to recent history.</p>
            </div>
            <button type="button" onClick={onCheckAll} disabled={isCheckingAll}>
              {isCheckingAll ? "Checking All..." : "Check All Saved Sites"}
            </button>
          </div>

          {checkAllMessage && <p className="error-message">{checkAllMessage}</p>}
          {checkAllResult && <CheckAllSummary summary={checkAllResult} />}

          <div className="site-list">
            {sites.map((site) => (
              <SavedSiteCard
                key={site.id}
                site={site}
                isChecking={checkingSiteId === site.id}
                isDeleting={deletingSiteId === site.id}
                onCheck={onCheck}
                onDelete={onDelete}
              />
            ))}
          </div>
        </>
      )}
    </section>
  );
}

function CheckAllSummary({ summary }) {
  return (
    <article className="check-all-summary">
      <div className="result-summary" aria-label="Check all summary">
        <SummaryItem label="Total" value={summary.total} />
        <SummaryItem label="Up" value={summary.up} />
        <SummaryItem label="Down" value={summary.down} />
      </div>

      {summary.results.length > 0 && (
        <div className="check-all-results">
          {summary.results.map((result) => (
            <div className="check-all-result" key={result.site_id}>
              <div>
                <h4>{result.name || result.hostname || result.normalized_url}</h4>
                <p>{result.normalized_url}</p>
              </div>
              <StatusBadge isUp={result.is_up} />
              <dl>
                <div>
                  <dt>HTTP</dt>
                  <dd>{result.status_code ?? "Not available"}</dd>
                </div>
                <div>
                  <dt>Response</dt>
                  <dd>{formatResponseTime(result.response_time_ms) ?? "Not available"}</dd>
                </div>
                <div>
                  <dt>Error</dt>
                  <dd>{result.error ?? "None"}</dd>
                </div>
              </dl>
            </div>
          ))}
        </div>
      )}
    </article>
  );
}

function SavedSiteCard({ site, isChecking, isDeleting, onCheck, onDelete }) {
  return (
    <article className="site-card">
      <div className="site-card-main">
        <h3>{site.name || site.hostname}</h3>
        <p className="site-url">{site.normalized_url}</p>
        <dl className="site-meta">
          <div>
            <dt>Host</dt>
            <dd>{site.hostname}</dd>
          </div>
          <div>
            <dt>Created</dt>
            <dd>{formatDate(site.created_at) ?? "Not available"}</dd>
          </div>
        </dl>
      </div>
      <div className="site-actions">
        <button type="button" onClick={() => onCheck(site)} disabled={isChecking || isDeleting}>
          {isChecking ? "Checking..." : "Check Site"}
        </button>
        <button
          type="button"
          className="danger-button"
          onClick={() => onDelete(site.id)}
          disabled={isChecking || isDeleting}
        >
          {isDeleting ? "Deleting..." : "Delete"}
        </button>
      </div>
    </article>
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

function HistorySection({
  history,
  total,
  hasMore,
  isLoading,
  isLoadingMore,
  isClearing,
  message,
  notice,
  onRefresh,
  onLoadMore,
  onClear,
}) {
  return (
    <section className="history-panel" aria-label="Recent check history">
      <div className="history-header">
        <div>
          <p className="section-label">Recent History</p>
          <h2>Saved Checks</h2>
        </div>
        <div className="section-actions">
          <button type="button" className="secondary-button" onClick={onRefresh} disabled={isLoading || isClearing}>
            {isLoading ? "Refreshing..." : "Refresh History"}
          </button>
          <button type="button" className="danger-button" onClick={onClear} disabled={isClearing || isLoading}>
            {isClearing ? "Clearing..." : "Clear History"}
          </button>
        </div>
      </div>

      {isLoading && <p className="status-message">Loading recent checks...</p>}
      {notice && <p className="success-message">{notice}</p>}
      {message && <p className="error-message">{message}</p>}
      {!isLoading && !message && history.length === 0 && (
        <p className="empty-message">No saved checks yet.</p>
      )}
      {!message && history.length > 0 && (
        <>
          <p className="history-count">
            Showing {history.length} of {total} checks
          </p>
          <HistoryTable history={history} />
          {hasMore && (
            <button
              type="button"
              className="load-more-button secondary-button"
              onClick={onLoadMore}
              disabled={isLoadingMore || isLoading || isClearing}
            >
              {isLoadingMore ? "Loading..." : "Load More"}
            </button>
          )}
        </>
      )}
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
