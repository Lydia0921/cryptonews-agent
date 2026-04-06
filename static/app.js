const PAGE_SIZE = 20;

let currentPage = 1;
let totalArticles = 0;
let isLoading = false;
let debounceTimer = null;

// ── Init ──────────────────────────────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", () => {
  resetAndLoad();
  loadTicker();
});

// ── Data loading ──────────────────────────────────────────────────────────────

function getFilters() {
  return {
    sentiment: document.getElementById("filter-sentiment").value,
    category: document.getElementById("filter-category").value,
    coin_symbol: document.getElementById("filter-coin").value.trim().toUpperCase(),
    is_relevant: document.getElementById("filter-relevant").checked ? "true" : "",
  };
}

function buildUrl(page) {
  const f = getFilters();
  const params = new URLSearchParams({ page, page_size: PAGE_SIZE });
  if (f.sentiment) params.set("sentiment", f.sentiment);
  if (f.category) params.set("category", f.category);
  if (f.coin_symbol) params.set("coin_symbol", f.coin_symbol);
  if (f.is_relevant) params.set("is_relevant", f.is_relevant);
  return `/api/news?${params}`;
}

async function fetchNews(page) {
  const res = await fetch(buildUrl(page));
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

function resetAndLoad() {
  currentPage = 1;
  totalArticles = 0;
  document.getElementById("news-list").innerHTML = "";
  document.getElementById("empty").style.display = "none";
  document.getElementById("load-more").style.display = "none";
  loadPage(1, true);
}

function debounceLoad() {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(resetAndLoad, 400);
}

async function loadPage(page, replace = false) {
  if (isLoading) return;
  isLoading = true;
  setLoadMoreDisabled(true);

  try {
    const data = await fetchNews(page);
    totalArticles = data.total;

    if (replace) {
      document.getElementById("news-list").innerHTML = "";
    }

    if (data.results.length === 0 && page === 1) {
      document.getElementById("empty").style.display = "block";
      document.getElementById("stats").textContent = "";
    } else {
      document.getElementById("empty").style.display = "none";
      document.getElementById("stats").textContent =
        `Showing ${Math.min(page * PAGE_SIZE, totalArticles)} of ${totalArticles} articles`;
      renderCards(data.results);
    }

    const loaded = page * PAGE_SIZE;
    if (loaded < totalArticles) {
      document.getElementById("load-more").style.display = "block";
      setLoadMoreDisabled(false);
    } else {
      document.getElementById("load-more").style.display = "none";
    }

    updateLastUpdated();
  } catch (err) {
    showToast("Failed to load news: " + err.message, true);
  } finally {
    isLoading = false;
  }
}

function loadMore() {
  currentPage += 1;
  loadPage(currentPage, false);
}

// ── Rendering ─────────────────────────────────────────────────────────────────

function renderCards(articles) {
  const list = document.getElementById("news-list");
  articles.forEach((a) => {
    list.insertAdjacentHTML("beforeend", cardHTML(a));
  });
}

function cardHTML(a) {
  const pub = a.published_at
    ? new Date(a.published_at).toLocaleString("en-US", {
        month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
      })
    : "—";

  const sentimentBadge = a.sentiment
    ? `<span class="badge badge-${a.sentiment}">${a.sentiment}</span>`
    : "";

  const coinBadge = a.coin_symbol
    ? `<span class="coin">${a.coin_symbol}</span>`
    : "";

  const score = a.relevance_score != null
    ? `<span class="score">Score ${(a.relevance_score * 10).toFixed(0)}/10</span>`
    : "";

  const categoryLabel = a.category
    ? `<span>${a.category}</span>`
    : "";

  return `
    <div class="news-card">
      <div>
        <div class="card-title">
          <a href="${escapeHtml(a.url)}" target="_blank" rel="noopener">${escapeHtml(a.title)}</a>
        </div>
        <div class="card-meta">
          <span>${escapeHtml(a.source || "unknown")}</span>
          <span>${pub}</span>
          ${categoryLabel}
        </div>
      </div>
      <div class="card-badges">
        ${sentimentBadge}
        ${coinBadge}
        ${score}
      </div>
    </div>`;
}

// ── Price ticker ─────────────────────────────────────────────────────────────

async function loadTicker() {
  try {
    const res = await fetch("/api/prices");
    if (!res.ok) return;
    const coins = await res.json();
    if (!coins.length) return;

    const items = coins.map((c) => {
      const p = c.price_usd;
      const price = p == null ? "—"
        : p >= 1      ? "$" + p.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })
        : p >= 0.0001 ? "$" + p.toFixed(6)
        : "$" + p.toExponential(2);
      const change = c.change_24h != null ? c.change_24h : null;
      const changeClass = change == null ? "" : change >= 0 ? "ticker-up" : "ticker-down";
      const changeStr = change == null ? "" : (change >= 0 ? "+" : "") + change.toFixed(2) + "%";
      return `<div class="ticker-item">
        <span class="ticker-symbol">${escapeHtml(c.symbol)}</span>
        <span class="ticker-price">${price}</span>
        ${changeStr ? `<span class="${changeClass}">${changeStr}</span>` : ""}
      </div>`;
    }).join("");

    // duplicate for seamless loop
    document.getElementById("ticker-track").innerHTML = items + items;
    document.getElementById("ticker-bar").style.display = "flex";
  } catch (err) {
    console.error("Ticker failed:", err);
  }
}

// ── Monitor trigger ───────────────────────────────────────────────────────────

async function triggerMonitor() {
  const btn = document.getElementById("trigger-btn");
  btn.disabled = true;
  btn.textContent = "Fetching…";

  try {
    const res = await fetch("/api/monitor/trigger", { method: "POST" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    showToast(`Done — ${data.added} new article${data.added !== 1 ? "s" : ""} added`);
    if (data.added > 0) resetAndLoad();
  } catch (err) {
    showToast("Trigger failed: " + err.message, true);
  } finally {
    btn.disabled = false;
    btn.textContent = "↻ Fetch News";
  }
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function setLoadMoreDisabled(val) {
  const btn = document.getElementById("load-more-btn");
  if (btn) btn.disabled = val;
}

function updateLastUpdated() {
  document.getElementById("last-updated").textContent =
    "Updated " + new Date().toLocaleTimeString();
}

function showToast(msg, isError = false) {
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.className = "toast show" + (isError ? " error" : "");
  setTimeout(() => { el.className = "toast"; }, 3000);
}

// ── Q&A ───────────────────────────────────────────────────────────────────────

async function askQuestion() {
  const input = document.getElementById("qa-input");
  const btn = document.getElementById("qa-btn");
  const question = input.value.trim();
  if (!question) return;

  btn.disabled = true;
  btn.textContent = "Thinking…";

  try {
    const res = await fetch("/api/qa", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    document.getElementById("qa-answer").textContent = data.answer;

    const sourcesEl = document.getElementById("qa-sources");
    if (data.articles && data.articles.length > 0) {
      sourcesEl.innerHTML =
        `<div class="qa-sources-label">Sources:</div>` +
        data.articles
          .map((a) => `<a href="${escapeHtml(a.url)}" target="_blank" rel="noopener">${escapeHtml(a.title)}</a>`)
          .join("");
    } else {
      sourcesEl.innerHTML = "";
    }

    document.getElementById("qa-result").style.display = "block";
  } catch (err) {
    showToast("QA failed: " + err.message, true);
  } finally {
    btn.disabled = false;
    btn.textContent = "Ask";
  }
}

function escapeHtml(str) {
  if (!str) return "";
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}
