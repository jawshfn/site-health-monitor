import React, { useEffect, useState } from "react";
import "./App.css";

const LOCAL_API_BASE_URL = "http://127.0.0.1:8000";
const CONFIGURED_API_BASE_URL = import.meta.env.VITE_API_BASE_URL?.trim();
const API_BASE_URL = CONFIGURED_API_BASE_URL || (import.meta.env.DEV ? LOCAL_API_BASE_URL : "");
const HISTORY_PAGE_SIZE = 10;
const BACKEND_UNAVAILABLE_MESSAGE = API_BASE_URL
  ? `Could not reach the backend API at ${API_BASE_URL}. Run the FastAPI backend locally to perform live checks.`
  : "The backend API is not connected in this static demo. Run the FastAPI backend locally to perform live checks.";

class BackendUnavailableError extends Error {}

function buildApiUrl(path) {
  return `${API_BASE_URL}${path}`;
}

async function apiFetch(path, options) {
  if (!API_BASE_URL) {
    throw new BackendUnavailableError(BACKEND_UNAVAILABLE_MESSAGE);
  }

  return fetch(buildApiUrl(path), options);
}

function getRequestErrorMessage(error, fallbackMessage) {
  if (error instanceof BackendUnavailableError || error instanceof TypeError) {
    return BACKEND_UNAVAILABLE_MESSAGE;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return fallbackMessage;
}

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
  const [editingSiteId, setEditingSiteId] = useState(null);
  const [editingSiteName, setEditingSiteName] = useState("");
  const [savingSiteNameId, setSavingSiteNameId] = useState(null);
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
  const [historySearch, setHistorySearch] = useState("");
  const [historyStatus, setHistoryStatus] = useState("");
  const [summary, setSummary] = useState(null);
  const [isSummaryLoading, setIsSummaryLoading] = useState(false);
  const [summaryMessage, setSummaryMessage] = useState("");

  useEffect(() => {
    loadSummary();
    loadHistory();
    loadSavedSites();
  }, []);

  function clearCheckAllResults() {
    setCheckAllResult(null);
    setCheckAllMessage("");
  }

  async function loadSummary() {
    setIsSummaryLoading(true);
    setSummaryMessage("");

    try {
      const response = await apiFetch("/api/summary");

      if (!response.ok) {
        throw new Error(`Summary request failed with status ${response.status}.`);
      }

      const data = await response.json();
      setSummary(data);
    } catch (error) {
      setSummaryMessage(getRequestErrorMessage(
        error,
        "Could not load dashboard summary. Run the FastAPI backend locally to view live data."
      )
      );
    } finally {
      setIsSummaryLoading(false);
    }
  }

  async function loadHistory({
    offset = 0,
    append = false,
    status = historyStatus,
    search = historySearch,
  } = {}) {
    if (append) {
      setIsLoadingMoreHistory(true);
    } else {
      setIsHistoryLoading(true);
    }
    setHistoryMessage("");
    setHistoryNotice("");

    try {
      const query = new URLSearchParams({
        limit: String(HISTORY_PAGE_SIZE),
        offset: String(offset),
      });
      const cleanedStatus = status.trim();
      const cleanedSearch = search.trim();

      if (cleanedStatus) {
        query.set("status_label", cleanedStatus);
      }

      if (cleanedSearch.length >= 2) {
        query.set("search", cleanedSearch);
      }

      const response = await apiFetch(`/api/history?${query.toString()}`);

      if (!response.ok) {
        throw new Error(`History request failed with status ${response.status}.`);
      }

      const data = await response.json();
      setHistory((currentHistory) => (append ? [...currentHistory, ...data.items] : data.items));
      setHistoryTotal(data.total);
      setHasMoreHistory(data.has_more);
    } catch (error) {
      setHistoryMessage(getRequestErrorMessage(
        error,
        "Could not load recent history. Run the FastAPI backend locally to view live data."
      )
      );
    } finally {
      setIsHistoryLoading(false);
      setIsLoadingMoreHistory(false);
    }
  }

  function updateHistorySearch(value) {
    setHistorySearch(value);
    loadHistory({ search: value, status: historyStatus });
  }

  function updateHistoryStatus(value) {
    setHistoryStatus(value);
    loadHistory({ status: value, search: historySearch });
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
      const response = await apiFetch("/api/history", {
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
      await loadSummary();
    } catch (error) {
      setHistoryMessage(getRequestErrorMessage(
        error,
        "Could not clear history. Run the FastAPI backend locally to manage history."
      )
      );
    } finally {
      setIsClearingHistory(false);
    }
  }

  async function loadSavedSites() {
    setIsSitesLoading(true);
    setSitesMessage("");

    try {
      const response = await apiFetch("/api/sites");

      if (!response.ok) {
        throw new Error(`Saved sites request failed with status ${response.status}.`);
      }

      const data = await response.json();
      setSavedSites(data);
      setEditingSiteId(null);
      setEditingSiteName("");
      clearCheckAllResults();
      await loadSummary();
    } catch (error) {
      setSitesMessage(getRequestErrorMessage(
        error,
        "Could not load saved sites. Run the FastAPI backend locally to view live data."
      )
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
      const response = await apiFetch("/api/sites", {
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
      setSitesMessage(getRequestErrorMessage(
        error,
        "Could not save the site. Run the FastAPI backend locally to manage saved sites."
      )
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
      await loadSummary();
    } catch (error) {
      setMessage(getRequestErrorMessage(
        error,
        "Could not check the saved site. Run the FastAPI backend locally to perform live checks."
      )
      );
    } finally {
      setCheckingSiteId(null);
    }
  }

  async function deleteSavedSite(siteId) {
    setDeletingSiteId(siteId);
    setSitesMessage("");

    try {
      const response = await apiFetch(`/api/sites/${siteId}`, {
        method: "DELETE",
      });

      if (!response.ok) {
        throw new Error(`Delete failed with status ${response.status}.`);
      }

      setSavedSites((currentSites) => currentSites.filter((site) => site.id !== siteId));
      clearCheckAllResults();
      await loadSummary();
    } catch (error) {
      setSitesMessage(getRequestErrorMessage(
        error,
        "Could not delete the saved site. Run the FastAPI backend locally to manage saved sites."
      )
      );
    } finally {
      setDeletingSiteId(null);
    }
  }

  function startEditingSite(site) {
    setEditingSiteId(site.id);
    setEditingSiteName(site.name ?? "");
    setSitesMessage("");
  }

  function cancelEditingSite() {
    setEditingSiteId(null);
    setEditingSiteName("");
    setSitesMessage("");
  }

  async function updateSavedSiteName(siteId) {
    setSavingSiteNameId(siteId);
    setSitesMessage("");

    try {
      const response = await apiFetch(`/api/sites/${siteId}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name: editingSiteName,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.detail ?? `Update failed with status ${response.status}.`);
      }

      const updatedSite = await response.json();
      setSavedSites((currentSites) =>
        currentSites.map((site) => (site.id === updatedSite.id ? updatedSite : site))
      );
      setEditingSiteId(null);
      setEditingSiteName("");
      clearCheckAllResults();
      await loadSummary();
    } catch (error) {
      setSitesMessage(getRequestErrorMessage(
        error,
        "Could not update the saved site. Run the FastAPI backend locally to manage saved sites."
      )
      );
    } finally {
      setSavingSiteNameId(null);
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
      const response = await apiFetch("/api/sites/check-all", {
        method: "POST",
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.detail ?? `Check all failed with status ${response.status}.`);
      }

      const data = await response.json();
      setCheckAllResult(data);
      await loadHistory();
      await loadSummary();
    } catch (error) {
      setCheckAllMessage(getRequestErrorMessage(
        error,
        "Could not check saved sites. Run the FastAPI backend locally to perform live checks."
      )
      );
    } finally {
      setIsCheckingAllSites(false);
    }
  }

  async function checkUrl(urlToCheck) {
    const response = await apiFetch("/api/check", {
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
      await loadSummary();
    } catch (error) {
      setMessage(getRequestErrorMessage(
        error,
        "Could not check the site. Run the FastAPI backend locally to perform live checks."
      )
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

      {!API_BASE_URL && <StaticDemoNotice />}

      <DashboardSummary
        summary={summary}
        isLoading={isSummaryLoading}
        message={summaryMessage}
      />

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
          <p className="observation-note">
            Results show what this checker observed. Some websites may block automated
            requests, use CDN protection, or respond differently by region or timeout.
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
        editingSiteId={editingSiteId}
        editingSiteName={editingSiteName}
        savingSiteNameId={savingSiteNameId}
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
        onStartEdit={startEditingSite}
        onEditNameChange={setEditingSiteName}
        onSaveEdit={updateSavedSiteName}
        onCancelEdit={cancelEditingSite}
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
        search={historySearch}
        status={historyStatus}
        onRefresh={loadHistory}
        onLoadMore={() => loadHistory({ offset: history.length, append: true })}
        onClear={clearHistory}
        onSearchChange={updateHistorySearch}
        onStatusChange={updateHistoryStatus}
      />
    </main>
  );
}

function StaticDemoNotice() {
  return (
    <section className="demo-notice" aria-label="Static demo notice">
      <h2>Frontend-only demo</h2>
      <p>
        This GitHub Pages version shows the React interface, but the backend API is not
        connected. Run the FastAPI backend locally to perform live website checks,
        load saved sites, and view check history.
      </p>
    </section>
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
  editingSiteId,
  editingSiteName,
  savingSiteNameId,
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
  onStartEdit,
  onEditNameChange,
  onSaveEdit,
  onCancelEdit,
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
                isEditing={editingSiteId === site.id}
                editName={editingSiteName}
                isSavingName={savingSiteNameId === site.id}
                onCheck={onCheck}
                onDelete={onDelete}
                onStartEdit={onStartEdit}
                onEditNameChange={onEditNameChange}
                onSaveEdit={onSaveEdit}
                onCancelEdit={onCancelEdit}
              />
            ))}
          </div>
        </>
      )}
    </section>
  );
}

function DashboardSummary({ summary, isLoading, message }) {
  const items = [
    {
      label: "Saved Sites",
      value: summary?.saved_sites_count ?? 0,
      helper: "In watchlist",
    },
    {
      label: "Total Checks",
      value: summary?.total_checks ?? 0,
      helper: "Saved results",
    },
    {
      label: "Latest Healthy",
      value: summary?.latest_up_count ?? 0,
      helper: "Newest status per site",
    },
    {
      label: "Latest Issues",
      value: summary?.latest_down_count ?? 0,
      helper: "Newest status per site",
    },
    {
      label: "Avg Response",
      value: formatResponseTime(summary?.average_response_time_ms) ?? "Not available",
      helper: "Checks with response time",
    },
  ];

  return (
    <section className="summary-panel" aria-label="Dashboard summary">
      <div className="summary-header">
        <div>
          <p className="section-label">Dashboard</p>
          <h2>Monitoring Summary</h2>
        </div>
        {isLoading && <span className="summary-loading">Updating...</span>}
      </div>

      {message && <p className="error-message">{message}</p>}

      <div className="dashboard-grid">
        {items.map((item) => (
          <article className="dashboard-card" key={item.label}>
            <span>{item.label}</span>
            <strong>{item.value}</strong>
            <p>{item.helper}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

function CheckAllSummary({ summary }) {
  return (
    <article className="check-all-summary">
      <div className="result-summary" aria-label="Check all summary">
        <SummaryItem label="Total" value={summary.total} />
        <SummaryItem label="Healthy" value={summary.up} />
        <SummaryItem label="Issues" value={summary.down} />
      </div>

      {summary.results.length > 0 && (
        <div className="check-all-results">
          {summary.results.map((result) => (
            <div className="check-all-result" key={result.site_id}>
              <div>
                <h4>{result.name || result.hostname || result.normalized_url}</h4>
                <p>{result.normalized_url}</p>
              </div>
              <StatusBadge result={result} />
              <dl>
                <div>
                  <dt>HTTP</dt>
                  <dd>{formatHttpStatus(result)}</dd>
                </div>
                <div>
                  <dt>Response</dt>
                  <dd>{formatResponseTime(result.response_time_ms) ?? "Not available"}</dd>
                </div>
                <div>
                  <dt>Error</dt>
                  <dd>{result.error ?? "None"}</dd>
                </div>
                <div>
                  <dt>Diagnostics</dt>
                  <dd>{result.diagnostic_summary ?? "Not available"}</dd>
                </div>
              </dl>
            </div>
          ))}
        </div>
      )}
    </article>
  );
}

function SavedSiteCard({
  site,
  isChecking,
  isDeleting,
  isEditing,
  editName,
  isSavingName,
  onCheck,
  onDelete,
  onStartEdit,
  onEditNameChange,
  onSaveEdit,
  onCancelEdit,
}) {
  function handleEditSubmit(event) {
    event.preventDefault();
    onSaveEdit(site.id);
  }

  return (
    <article className="site-card">
      <div className="site-card-main">
        {isEditing ? (
          <form className="site-edit-form" onSubmit={handleEditSubmit}>
            <label htmlFor={`site-name-${site.id}`}>Friendly name</label>
            <input
              id={`site-name-${site.id}`}
              type="text"
              value={editName}
              onChange={(event) => onEditNameChange(event.target.value)}
              placeholder="Optional display name"
              disabled={isSavingName}
            />
            <div className="site-edit-actions">
              <button type="submit" disabled={isSavingName || isChecking || isDeleting}>
                {isSavingName ? "Saving..." : "Save"}
              </button>
              <button
                type="button"
                className="secondary-button"
                onClick={onCancelEdit}
                disabled={isSavingName}
              >
                Cancel
              </button>
            </div>
          </form>
        ) : (
          <h3>{site.name || site.hostname}</h3>
        )}
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
        <button
          type="button"
          onClick={() => onCheck(site)}
          disabled={isChecking || isDeleting || isEditing}
        >
          {isChecking ? "Checking..." : "Check Site"}
        </button>
        <button
          type="button"
          className="secondary-button"
          onClick={() => onStartEdit(site)}
          disabled={isChecking || isDeleting || isEditing}
        >
          Edit Name
        </button>
        <button
          type="button"
          className="danger-button"
          onClick={() => onDelete(site.id)}
          disabled={isChecking || isDeleting || isEditing}
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
        <StatusBadge result={result} />
      </div>

      <div className="result-summary" aria-label="Result summary">
        <SummaryItem label="Status" value={getStatusText(result)} />
        <SummaryItem label="HTTP" value={formatHttpStatus(result)} />
        <SummaryItem
          label="Response"
          value={formatResponseTime(result.response_time_ms) ?? "Not available"}
        />
      </div>

      <div className="diagnostics-box" aria-label="Reachability diagnostics">
        <h3>Reachability Diagnostics</h3>
        <div className="diagnostics-grid">
          <SummaryItem label="DNS" value={formatDiagnosticStatus(result.dns_status)} />
          <SummaryItem
            label="Connection"
            value={formatDiagnosticStatus(result.connection_status)}
          />
          <SummaryItem label="HTTP" value={formatDiagnosticStatus(result.http_status)} />
        </div>
        <p>{result.diagnostic_summary ?? "No diagnostic summary is available."}</p>
      </div>

      <dl className="result-grid">
        <ResultRow label="Input URL" value={result.input_url} />
        <ResultRow label="Normalized URL" value={result.normalized_url} />
        <ResultRow label="Final URL" value={result.final_url} />
        <ResultRow label="Hostname" value={result.hostname} />
        <ResultRow label="Observed Result" value={getStatusText(result)} />
        <ResultRow label="Status Code" value={formatHttpStatus(result)} />
        <ResultRow label="Response Time" value={formatResponseTime(result.response_time_ms)} />
        <ResultRow label="IP Addresses" value={formatIpAddresses(result.ip_addresses)} />
        <ResultRow label="Checked At" value={formatDate(result.checked_at)} />
        {result.error && <ResultRow label="Error" value={result.error} />}
      </dl>
      {!result.is_up && <p className="result-note">{getStatusExplanation(result)}</p>}
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
  search,
  status,
  onRefresh,
  onLoadMore,
  onClear,
  onSearchChange,
  onStatusChange,
}) {
  const hasActiveSearch = search.trim().length >= 2;
  const hasActiveFilters = hasActiveSearch || status;

  return (
    <section className="history-panel" aria-label="Recent check history">
      <div className="history-header">
        <div>
          <p className="section-label">Recent History</p>
          <h2>Previous Checks</h2>
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

      <div className="history-filters" aria-label="History filters">
        <div className="history-filter-field">
          <label htmlFor="history-search">Search hostname or URL</label>
          <input
            id="history-search"
            type="search"
            value={search}
            onChange={(event) => onSearchChange(event.target.value)}
            placeholder="example.com"
            aria-describedby="history-search-help"
            disabled={isClearing}
          />
          <p id="history-search-help" className="field-help">
            Enter at least 2 characters to search.
          </p>
        </div>
        <div className="history-filter-field">
          <label htmlFor="history-status">Observed status</label>
          <select
            id="history-status"
            value={status}
            onChange={(event) => onStatusChange(event.target.value)}
            disabled={isClearing}
          >
            <option value="">All statuses</option>
            <option value="healthy">Healthy</option>
            <option value="issue">Issues</option>
            <option value="http_error">HTTP Error</option>
            <option value="timeout">Timed Out</option>
            <option value="dns_error">DNS Failed</option>
          </select>
        </div>
      </div>

      {isLoading && <p className="status-message">Loading recent checks...</p>}
      {notice && <p className="success-message">{notice}</p>}
      {message && <p className="error-message">{message}</p>}
      {!isLoading && !message && history.length === 0 && (
        <p className="empty-message">
          {hasActiveFilters ? "No saved checks match the current filters." : "No saved checks yet."}
        </p>
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
            <th scope="col">Site</th>
            <th scope="col">Status</th>
            <th scope="col">HTTP</th>
            <th scope="col">Response</th>
            <th scope="col">Checked</th>
          </tr>
        </thead>
        <tbody>
          {history.map((check) => (
            <React.Fragment key={check.id}>
              <tr className="history-main-row">
                <td data-label="Site" className="site-cell">
                  <strong>{check.hostname ?? "Not available"}</strong>
                  <span>{check.normalized_url ?? check.input_url ?? "Not available"}</span>
                </td>
                <td data-label="Status" className="status-cell">
                  <StatusBadge result={check} />
                </td>
                <td data-label="HTTP" className="http-cell">
                  {formatHttpStatus(check)}
                </td>
                <td data-label="Response" className="time-cell">
                  {formatResponseTime(check.response_time_ms) ?? "Not available"}
                </td>
                <td data-label="Checked" className="checked-cell">
                  {formatDate(check.checked_at) ?? "Not available"}
                </td>
              </tr>
              <tr className="history-details-row">
                <td colSpan="5">
                  <span>Details:</span> {check.diagnostic_summary ?? check.error ?? "None"}
                </td>
              </tr>
            </React.Fragment>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function StatusBadge({ result }) {
  const isHealthy = result?.is_up === true;
  const statusText = getStatusText(result);

  return (
    <span className={isHealthy ? "badge badge-up" : "badge badge-issue"}>
      <span aria-hidden="true">{isHealthy ? "OK" : "!"}</span>
      {statusText}
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

function formatHttpStatus(result) {
  if (!result || result.status_code === null || result.status_code === undefined) {
    return result?.status_label === "timeout" ? "No response" : "Not available";
  }

  return result.status_code;
}

function formatDiagnosticStatus(value) {
  const labels = {
    resolved: "Resolved",
    failed: "Failed",
    connected: "Connected",
    response_received: "Response Received",
    timeout: "Timed Out",
    not_checked: "Not Checked",
    not_attempted: "Not Attempted",
  };

  return labels[value] ?? "Not Available";
}

function getStatusText(result) {
  const labels = {
    healthy: "Healthy",
    http_error: "HTTP Error",
    timeout: "Timed Out",
    dns_error: "DNS Failed",
    connection_error: "Connection Failed",
    invalid_url: "Invalid URL",
    unknown_error: "Unknown Error",
  };

  return labels[result?.status_label] ?? (result?.is_up ? "Healthy" : "Unknown Error");
}

function getStatusExplanation(result) {
  const explanations = {
    http_error: "The server responded, but the checked URL returned a non-success status.",
    timeout: "No HTTP response was received before the timeout. The site may still be online.",
    dns_error: "The hostname could not be resolved by this checker.",
    connection_error: "This checker could not open an HTTP connection to the site.",
    invalid_url: "The submitted URL could not be checked.",
    unknown_error: "This checker encountered an unexpected error.",
  };

  return explanations[result?.status_label] ?? "This checker observed an issue with the request.";
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
