const pptxgen = require("pptxgenjs");

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.author = "Lisa";
pres.title = "Crypto News Monitor — Interview Presentation";

// ─── Palette ──────────────────────────────────────────────────────────────
const BG       = "0F172A"; // dark navy
const CARD     = "1E293B"; // card bg
const ACCENT   = "38BDF8"; // sky blue
const GREEN    = "34D399"; // emerald
const AMBER    = "F59E0B"; // amber
const TEXT     = "F8FAFC"; // near white
const MUTED    = "94A3B8"; // muted
const BEARISH  = "F87171"; // red

function sectionTag(slide, label) {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.4, y: 0.18, w: 1.6, h: 0.32,
    fill: { color: ACCENT }, rectRadius: 0.08,
  });
  slide.addText(label, {
    x: 0.4, y: 0.18, w: 1.6, h: 0.32,
    fontSize: 9, bold: true, color: BG,
    align: "center", valign: "middle", margin: 0,
  });
}

function slideTitle(slide, text) {
  slide.addText(text, {
    x: 0.4, y: 0.6, w: 9.2, h: 0.6,
    fontSize: 28, bold: true, color: TEXT,
    fontFace: "Arial", margin: 0,
  });
}

function card(slide, x, y, w, h, color) {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x, y, w, h,
    fill: { color: color || CARD },
    rectRadius: 0.12,
    shadow: { type: "outer", color: "000000", blur: 8, offset: 2, angle: 135, opacity: 0.3 },
  });
}

function hRule(slide, y) {
  slide.addShape(pres.shapes.LINE, {
    x: 0.4, y, w: 9.2, h: 0,
    line: { color: ACCENT, width: 1.5 },
  });
}

// ══════════════════════════════════════════════════════════════════════════
// Slide 1 — Title
// ══════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: BG };

  // Accent bar left
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 0.22, h: 5.625,
    fill: { color: ACCENT },
  });

  // Big title
  s.addText("Crypto News Monitor", {
    x: 0.5, y: 1.2, w: 9, h: 1.0,
    fontSize: 40, bold: true, color: TEXT,
    fontFace: "Arial", margin: 0,
  });

  // Subtitle
  s.addText("AI-Powered Regulatory & Market Sentiment Tracker", {
    x: 0.5, y: 2.25, w: 9, h: 0.5,
    fontSize: 18, color: ACCENT,
    fontFace: "Arial", margin: 0,
  });

  hRule(s, 2.9);

  // Tech stack pills
  const pills = [
    ["FastAPI", ACCENT],
    ["SQLite", GREEN],
    ["Gemini 2.5 Flash", AMBER],
    ["NewsData.io", MUTED],
    ["Claude Code", "C084FC"],
  ];
  let px = 0.5;
  pills.forEach(([label, color]) => {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: px, y: 3.15, w: label.length * 0.13 + 0.5, h: 0.32,
      fill: { color }, rectRadius: 0.08,
    });
    s.addText(label, {
      x: px, y: 3.15, w: label.length * 0.13 + 0.5, h: 0.32,
      fontSize: 10, bold: true, color: BG,
      align: "center", valign: "middle", margin: 0,
    });
    px += label.length * 0.13 + 0.65;
  });

  // Bottom tagline
  s.addText("5-min Interview Walkthrough", {
    x: 0.5, y: 4.9, w: 9, h: 0.4,
    fontSize: 11, color: MUTED, italic: true,
    align: "left", margin: 0,
  });
}

// ══════════════════════════════════════════════════════════════════════════
// Slide 2 — Project Overview
// ══════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: BG };
  sectionTag(s, "OVERVIEW");
  slideTitle(s, "專案概覽");
  hRule(s, 1.35);

  // Left column — Features
  card(s, 0.4, 1.55, 4.3, 3.7);
  s.addText("核心功能", {
    x: 0.65, y: 1.7, w: 3.8, h: 0.38,
    fontSize: 13, bold: true, color: ACCENT, margin: 0,
  });
  s.addText([
    { text: "監管新聞警報", options: { bullet: true, breakLine: true, bold: true, color: TEXT } },
    { text: "SEC、ETF、各國法規即時追蹤", options: { bullet: false, breakLine: true, color: MUTED, fontSize: 11 } },
    { text: "市場情緒分類", options: { bullet: true, breakLine: true, bold: true, color: TEXT } },
    { text: "Bullish / Bearish / Neutral 自動標記", options: { bullet: false, breakLine: true, color: MUTED, fontSize: 11 } },
    { text: "RAG 問答系統", options: { bullet: true, breakLine: true, bold: true, color: TEXT } },
    { text: "從 DB 檢索新聞並由 Gemini 回答", options: { bullet: false, breakLine: true, color: MUTED, fontSize: 11 } },
    { text: "即時價格 Ticker", options: { bullet: true, breakLine: true, bold: true, color: TEXT } },
    { text: "CoinGecko 整合，主流幣即時顯示", options: { bullet: false, color: MUTED, fontSize: 11 } },
  ], { x: 0.65, y: 2.15, w: 3.8, h: 2.9, fontSize: 13, fontFace: "Arial" });

  // Right column — Tech stack
  card(s, 4.9, 1.55, 4.7, 3.7);
  s.addText("技術棧", {
    x: 5.15, y: 1.7, w: 4.2, h: 0.38,
    fontSize: 13, bold: true, color: GREEN, margin: 0,
  });

  const tech = [
    ["後端", "Python + FastAPI + APScheduler", ACCENT],
    ["資料庫", "SQLite + SQLAlchemy ORM", GREEN],
    ["AI Agent", "Google Gemini 2.5 Flash", AMBER],
    ["新聞來源", "NewsData.io Crypto API", MUTED],
    ["前端", "原生 HTML / JS（無框架）", "C084FC"],
    ["開發工具", "Claude Code（AI-assisted）", "38BDF8"],
  ];
  tech.forEach(([key, val, color], i) => {
    s.addShape(pres.shapes.RECTANGLE, {
      x: 5.15, y: 2.15 + i * 0.52, w: 0.06, h: 0.3,
      fill: { color },
    });
    s.addText(key, {
      x: 5.28, y: 2.15 + i * 0.52, w: 1.0, h: 0.3,
      fontSize: 11, bold: true, color, margin: 0, valign: "middle",
    });
    s.addText(val, {
      x: 6.35, y: 2.15 + i * 0.52, w: 3.0, h: 0.3,
      fontSize: 11, color: TEXT, margin: 0, valign: "middle",
    });
  });
}

// ══════════════════════════════════════════════════════════════════════════
// Slide 3 — System Architecture
// ══════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: BG };
  sectionTag(s, "ARCHITECTURE");
  slideTitle(s, "系統架構");
  hRule(s, 1.35);

  // Architecture: two rows
  // Row 1: Data pipeline — fetcher → analyzer → SQLite
  // Row 2: Serving — FastAPI → Frontend / QA Agent

  const boxW = 1.8;
  const boxH = 0.72;

  function archBox(s, x, y, label, sublabel, color) {
    card(s, x, y, boxW, boxH, CARD);
    s.addShape(pres.shapes.RECTANGLE, {
      x, y, w: 0.06, h: boxH,
      fill: { color },
    });
    s.addText(label, {
      x: x + 0.14, y: y + 0.06, w: boxW - 0.18, h: 0.3,
      fontSize: 12, bold: true, color, margin: 0,
    });
    s.addText(sublabel, {
      x: x + 0.14, y: y + 0.36, w: boxW - 0.18, h: 0.28,
      fontSize: 9, color: MUTED, margin: 0,
    });
  }

  function arrow(s, x1, y, x2) {
    s.addShape(pres.shapes.LINE, {
      x: x1, y, w: x2 - x1, h: 0,
      line: { color: MUTED, width: 1.5 },
    });
    // arrowhead via tiny triangle text
    s.addText("▶", {
      x: x2 - 0.2, y: y - 0.12, w: 0.22, h: 0.24,
      fontSize: 10, color: MUTED, margin: 0,
    });
  }

  function arrowDown(s, x, y1, y2) {
    s.addShape(pres.shapes.LINE, {
      x, y: y1, w: 0, h: y2 - y1,
      line: { color: MUTED, width: 1.5 },
    });
    s.addText("▼", {
      x: x - 0.11, y: y2 - 0.18, w: 0.22, h: 0.24,
      fontSize: 10, color: MUTED, margin: 0,
    });
  }

  // ── Data pipeline row (y=1.6) ──
  const row1y = 1.6;
  archBox(s, 0.3, row1y, "NewsData.io", "Crypto API", ACCENT);
  arrow(s, 0.3 + boxW, row1y + boxH / 2, 2.35);
  archBox(s, 2.35, row1y, "fetcher_agent", "HTTP + 去重", GREEN);
  arrow(s, 2.35 + boxW, row1y + boxH / 2, 4.4);
  archBox(s, 4.4, row1y, "analyzer_agent", "Gemini 分析", AMBER);
  arrow(s, 4.4 + boxW, row1y + boxH / 2, 6.45);
  archBox(s, 6.45, row1y, "SQLite DB", "news_articles", MUTED);

  // monitor_agent orchestrator label
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 2.35, y: 1.3, w: 4.55, h: 0.25,
    fill: { color: "1E293B" }, rectRadius: 0.06,
    line: { color: ACCENT, width: 0.5 },
  });
  s.addText("monitor_agent (orchestrator)", {
    x: 2.35, y: 1.3, w: 4.55, h: 0.25,
    fontSize: 9, color: ACCENT, align: "center", valign: "middle", margin: 0,
  });

  // ── Serving row (y=3.2) ──
  const row2y = 3.0;
  arrowDown(s, 6.45 + boxW / 2, row1y + boxH, row2y);
  archBox(s, 5.5, row2y, "FastAPI", "REST API", ACCENT);
  arrow(s, 5.5 + boxW, row2y + boxH / 2, 7.55);
  archBox(s, 7.55, row2y, "Frontend", "HTML / JS", "C084FC");

  // QA branch
  const qaY = 3.0;
  archBox(s, 0.3, qaY, "qa_agent", "RAG + Gemini", "F472B6");
  arrow(s, 0.3 + boxW, qaY + boxH / 2, 2.3);
  s.addShape(pres.shapes.LINE, {
    x: 2.5, y: qaY + boxH / 2, w: 0, h: -(qaY - row1y - boxH),
    line: { color: MUTED, width: 1, dashType: "dash" },
  });
  s.addText("reads", {
    x: 2.55, y: 2.45, w: 0.7, h: 0.22,
    fontSize: 9, color: MUTED, italic: true, margin: 0,
  });

  // Arrow from FastAPI to qa_agent
  s.addShape(pres.shapes.LINE, {
    x: 2.2, y: qaY + boxH / 2, w: 5.5 - 2.2, h: 0,
    line: { color: MUTED, width: 1, dashType: "dash" },
  });

  // Legend
  const legendItems = [
    ["Data Flow", ACCENT],
    ["AI Processing", AMBER],
    ["Storage", MUTED],
    ["Presentation", "C084FC"],
  ];
  legendItems.forEach(([label, color], i) => {
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.3 + i * 2.3, y: 4.95, w: 0.18, h: 0.18,
      fill: { color },
    });
    s.addText(label, {
      x: 0.55 + i * 2.3, y: 4.93, w: 1.8, h: 0.22,
      fontSize: 9, color: MUTED, margin: 0,
    });
  });
}

// ══════════════════════════════════════════════════════════════════════════
// Slide 4 — AI Tool Usage (Claude Code)
// ══════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: BG };
  sectionTag(s, "AI TOOLS");
  slideTitle(s, "Claude Code 使用方式");
  hRule(s, 1.35);

  const tools = [
    {
      name: "CLAUDE.md",
      color: ACCENT,
      desc: "專案說明書：技術棧、架構、API規範、Gemini用法、DB規範、NewsData.io限制全部文件化，讓 Claude 每次對話都有正確的 context。",
    },
    {
      name: "Skills",
      color: GREEN,
      desc: "4 個客製化 Skill：news-monitor-setup / relevance-analyzer / test-generator / report-formatter。重複性任務模板化，確保輸出一致。",
    },
    {
      name: "MCP SQLite",
      color: AMBER,
      desc: "直接在對話中查詢 news.db，不需開 terminal。可即時驗證資料、debug 查詢結果，加速開發迴圈。",
    },
    {
      name: "PreToolUse Hook",
      color: BEARISH,
      desc: "自動攔截所有檔案寫入操作，確保 Write / Edit / MultiEdit 只能修改專案目錄內的檔案。防止誤改系統檔。",
    },
    {
      name: "Subagents",
      color: "C084FC",
      desc: "將 monitor_agent 拆分為獨立的 fetcher_agent（HTTP 抓取 + 去重）和 analyzer_agent（Gemini 分析 + DB 寫入），由 orchestrator 串接。實現錯誤隔離，fetch 失敗不影響已完成的 analyze。",
    },
  ];

  tools.forEach((t, i) => {
    const y = 1.6 + i * 0.77;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: 0.4, y, w: 9.2, h: 0.65,
      fill: { color: CARD }, rectRadius: 0.1,
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.4, y: y + 0.08, w: 0.05, h: 0.49,
      fill: { color: t.color },
    });
    s.addText(t.name, {
      x: 0.6, y: y + 0.07, w: 1.7, h: 0.25,
      fontSize: 12, bold: true, color: t.color, margin: 0,
    });
    s.addText(t.desc, {
      x: 0.6, y: y + 0.32, w: 8.8, h: 0.28,
      fontSize: 10, color: MUTED, margin: 0,
    });
  });
}

// ══════════════════════════════════════════════════════════════════════════
// Slide 5 — Skills Design
// ══════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: BG };
  sectionTag(s, "SKILLS");
  slideTitle(s, "Skills 設計");
  hRule(s, 1.35);

  const skills = [
    {
      name: "news-monitor-setup",
      color: ACCENT,
      trigger: "「設定監控」/「新增監控需求」",
      purpose: "定義監控需求 → 產出關鍵字清單 + monitor_agent prompt 模板",
      impact: "需求變更時不需要手動重寫 prompt，減少人工 trial-and-error",
    },
    {
      name: "relevance-analyzer",
      color: GREEN,
      trigger: "審查相關性判斷邏輯時",
      purpose: "提供評分標準、情緒分類規則、Gemini prompt 設計原則與常見錯誤案例",
      impact: "Gemini 輸出品質一致，避免 prompt 版本混亂",
    },
    {
      name: "test-generator",
      color: AMBER,
      trigger: "新增 API endpoint 或 agent 功能後",
      purpose: "生成符合本專案風格的 pytest 測試：conftest fixture、mock Gemini、in-memory SQLite",
      impact: "測試覆蓋率提升，且不需每次重學 conftest 寫法",
    },
    {
      name: "report-formatter",
      color: "C084FC",
      trigger: "需要輸出報告 / debug 日誌",
      purpose: "統一新聞摘要、監控報告、QA 引用區塊、面試 demo 的輸出格式",
      impact: "展示文件格式一致，降低溝通成本",
    },
  ];

  skills.forEach((sk, i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const x = col === 0 ? 0.4 : 5.1;
    const y = 1.55 + row * 1.95;
    const w = 4.5;
    const h = 1.8;

    card(s, x, y, w, h);
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: x + 0.15, y: y + 0.15, w: w - 0.3, h: 0.3,
      fill: { color: sk.color }, rectRadius: 0.06,
    });
    s.addText(sk.name, {
      x: x + 0.15, y: y + 0.15, w: w - 0.3, h: 0.3,
      fontSize: 10, bold: true, color: BG,
      align: "center", valign: "middle", margin: 0,
    });
    s.addText("用途", {
      x: x + 0.15, y: y + 0.55, w: 0.5, h: 0.22,
      fontSize: 9, bold: true, color: sk.color, margin: 0,
    });
    s.addText(sk.purpose, {
      x: x + 0.65, y: y + 0.55, w: w - 0.8, h: 0.44,
      fontSize: 9, color: TEXT, margin: 0,
    });
    s.addText("效益", {
      x: x + 0.15, y: y + 1.1, w: 0.5, h: 0.22,
      fontSize: 9, bold: true, color: AMBER, margin: 0,
    });
    s.addText(sk.impact, {
      x: x + 0.65, y: y + 1.1, w: w - 0.8, h: 0.55,
      fontSize: 9, color: MUTED, margin: 0,
    });
  });
}

// ══════════════════════════════════════════════════════════════════════════
// Slide 6 — Risk Management
// ══════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: BG };
  sectionTag(s, "RISK MGMT");
  slideTitle(s, "風險管理");
  hRule(s, 1.35);

  const risks = [
    {
      icon: "🛡",
      title: "PreToolUse Hook — 寫入路徑保護",
      color: BEARISH,
      problem: "Claude 可能誤修改專案目錄外的系統檔案",
      solution: "攔截 Write/Edit/MultiEdit，驗證路徑在專案目錄內，否則 exit 2 阻擋",
      result: "所有檔案寫入受到邊界控制，誤操作前即時警告",
    },
    {
      icon: "🔌",
      title: "MCP SQLite — 安全的 DB 存取",
      color: ACCENT,
      problem: "直接拼接 SQL 字串有 SQL Injection 風險；手動 CLI 查詢容易出錯",
      solution: "SQLAlchemy ORM 防注入；MCP Server 提供結構化 query interface，限定操作範圍",
      result: "DB 操作可審計、可撤銷，不直接暴露 shell 權限",
    },
    {
      icon: "📐",
      title: "Structured Output — Gemini JSON 保證",
      color: GREEN,
      problem: "LLM 輸出非結構化文字時，解析失敗會導致資料寫入錯誤欄位",
      solution: "response_mime_type='application/json' + fallback 預設值，JSON 解析失敗時 gracefully 降級",
      result: "資料入庫穩定，不因 AI 輸出格式異常中斷整個 pipeline",
    },
  ];

  risks.forEach((r, i) => {
    const y = 1.55 + i * 1.32;
    card(s, 0.4, y, 9.2, 1.18);
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.4, y, w: 0.06, h: 1.18,
      fill: { color: r.color },
    });
    s.addText(r.title, {
      x: 0.65, y: y + 0.1, w: 8.7, h: 0.28,
      fontSize: 13, bold: true, color: r.color, margin: 0,
    });

    // Problem / Solution / Result in 3 columns
    const cols = [
      { label: "問題", text: r.problem, color: BEARISH },
      { label: "做法", text: r.solution, color: ACCENT },
      { label: "結果", text: r.result, color: GREEN },
    ];
    cols.forEach((c, j) => {
      const cx = 0.65 + j * 3.0;
      s.addText(c.label, {
        x: cx, y: y + 0.44, w: 0.5, h: 0.2,
        fontSize: 9, bold: true, color: c.color, margin: 0,
      });
      s.addText(c.text, {
        x: cx + 0.5, y: y + 0.44, w: 2.4, h: 0.65,
        fontSize: 9, color: MUTED, margin: 0,
      });
    });
  });
}

// ══════════════════════════════════════════════════════════════════════════
// Slide 7 — Limitations & Future Work
// ══════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: BG };
  sectionTag(s, "LIMITATIONS");
  slideTitle(s, "已知限制與改進方向");
  hRule(s, 1.35);

  const items = [
    {
      area: "語意搜尋",
      current: "Keyword ilike — 無法處理同義詞（BTC ≠ Bitcoin）",
      next: "加入 text-embedding-004 + cosine similarity 向量搜尋",
      color: ACCENT,
    },
    {
      area: "Startup Blocking",
      current: "初始 fetch 在 lifespan 同步執行，Gemini 分析期間 API 不回應",
      next: "改用 next_run_time=now() 讓 scheduler 在背景跑第一次",
      color: AMBER,
    },
    {
      area: "重複新聞",
      current: "同一事件被多家媒體轉載，各自存入 DB（url 去重只能防完全相同）",
      next: "Content fingerprint（SimHash）或 LLM 事件聚類",
      color: GREEN,
    },
    {
      area: "中文問答",
      current: "Gemini 中文理解較弱，RAG 效果不如英文",
      next: "換用 Claude API 或 Gemini 1.5 Pro（中文較強）",
      color: "F472B6",
    },
    {
      area: "Reranking",
      current: "取前 8 篇直接送 Gemini，無相關性排序",
      next: "Cross-encoder reranker 篩選最相關 3-4 篇，降低 context noise",
      color: "C084FC",
    },
  ];

  // Header row
  s.addText("面向", { x: 0.4, y: 1.48, w: 1.4, h: 0.25, fontSize: 9, bold: true, color: MUTED, margin: 0 });
  s.addText("現況", { x: 1.9, y: 1.48, w: 3.8, h: 0.25, fontSize: 9, bold: true, color: MUTED, margin: 0 });
  s.addText("改進方向", { x: 5.8, y: 1.48, w: 3.8, h: 0.25, fontSize: 9, bold: true, color: MUTED, margin: 0 });

  items.forEach((item, i) => {
    const y = 1.78 + i * 0.73;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: 0.4, y, w: 9.2, h: 0.62,
      fill: { color: CARD }, rectRadius: 0.08,
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.4, y: y + 0.1, w: 0.05, h: 0.42,
      fill: { color: item.color },
    });
    s.addText(item.area, {
      x: 0.55, y, w: 1.3, h: 0.62,
      fontSize: 11, bold: true, color: item.color,
      valign: "middle", margin: 0,
    });
    s.addText(item.current, {
      x: 1.9, y: y + 0.06, w: 3.75, h: 0.5,
      fontSize: 10, color: TEXT, margin: 0, valign: "middle",
    });
    s.addShape(pres.shapes.LINE, {
      x: 5.75, y: y + 0.08, w: 0, h: 0.46,
      line: { color: CARD, width: 1 },
    });
    s.addText(item.next, {
      x: 5.82, y: y + 0.06, w: 3.7, h: 0.5,
      fontSize: 10, color: GREEN, margin: 0, valign: "middle",
    });
  });
}

// ══════════════════════════════════════════════════════════════════════════
// Write file
// ══════════════════════════════════════════════════════════════════════════
pres.writeFile({ fileName: "crypto_news_monitor_interview.pptx" }).then(() => {
  console.log("✅ crypto_news_monitor_interview.pptx generated");
});
