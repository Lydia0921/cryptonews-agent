---
name: news-monitor-setup
description: 定義新聞監控需求，產出監控關鍵字清單與 monitor_agent 的 prompt 模板。當使用者說「設定監控」或「新增監控需求」時觸發。
---

# 新聞監控設定 Skill

## 觸發時機
- 使用者說「設定監控」、「新增監控需求」、「我想監控 XXX」

## 執行步驟

### Step 1 — 釐清監控需求

向使用者確認以下資訊（若已在訊息中提供則跳過）：

1. **監控主題**：要追蹤的公司、產業、事件類型？（例：台積電、AI 晶片、聯準會升息）
2. **相關性門檻**：只要提及就算，還是需要深度相關？
3. **排除條件**：哪些新聞不想看到？（例：業配、重複報導）
4. **語言偏好**：中文、英文、或兩者都要？

### Step 2 — 產出關鍵字清單

依照需求輸出三層關鍵字：

```
主要關鍵字（必須命中其中一個才進入判斷）：
- [keyword_1]
- [keyword_2]

次要關鍵字（提高相關性分數）：
- [keyword_3]
- [keyword_4]

排除關鍵字（命中則直接過濾）：
- [exclude_1]
```

### Step 3 — 產出 Gemini 相關性判斷 prompt 模板

輸出可直接貼入 `agents/monitor_agent.py` 的 prompt，格式如下：

```python
RELEVANCE_PROMPT = """
你是一個金融新聞分析師。請判斷以下新聞是否與「{topic}」相關。

新聞標題：{title}
新聞內文（前 500 字）：{content}

請以 JSON 格式回傳：
{{
  "is_relevant": true/false,
  "relevance_score": 0.0-1.0,
  "reason": "一句話說明判斷依據"
}}

判斷標準：
- 0.8 以上：直接且深度相關
- 0.5-0.8：間接相關或背景影響
- 0.5 以下：不相關
{additional_criteria}
"""
```

### Step 4 — 寫入設定（可選）

若使用者確認，將關鍵字清單以 JSON 格式輸出，可存入資料庫或設定檔：

```json
{
  "topic": "{topic}",
  "primary_keywords": [],
  "secondary_keywords": [],
  "exclude_keywords": [],
  "language": "zh/en/both",
  "min_relevance_score": 0.5
}
```
