# Chattie Python

Chattie Python 是 Chattie LINE 英文批改機器人的 Python 版本。服務提供兩種使用方式：

- LINE webhook：接收 LINE 訊息並回覆英文批改結果。
- HTTP API：透過 `POST /grade` 批改英文文字。

批改流程會先呼叫 LanguageTool 做文法與拼字檢查，再視規則決定是否呼叫 Anthropic LLM 產生改寫建議與學習提示。

## 專案結構

```text
chattie_py/
├── api/                 # HTTP API payload 驗證與批改入口
│   └── grading_api.py
├── config/              # 環境變數與常數設定
│   ├── constants.py
│   └── env.py
├── grading/             # 批改 pipeline、路由規則、輸出格式與資料型別
│   ├── formatter.py
│   ├── pipeline.py
│   ├── router.py
│   └── types.py
├── line/                # LINE webhook、簽章驗證、訊息過濾與回覆
│   ├── message_filter.py
│   ├── message_handler.py
│   ├── reply_helper.py
│   ├── signature_guard.py
│   └── webhook.py
├── llm/                 # Anthropic prompt、client 與回應解析
│   ├── client.py
│   ├── parser.py
│   └── prompt.py
├── nlp/                 # LanguageTool client 與 NLP 分數計算
│   ├── client.py
│   └── scorer.py
├── tests/               # 核心邏輯測試
│   └── test_core.py
├── utils/               # 共用錯誤、logger、文字工具
├── server.py            # HTTP server 與路由
├── pyproject.toml       # Python 專案設定
└── SDD.md               # 系統設計文件
```

## 需求

- Python 3.9+
- LINE Messaging API channel credentials
- Anthropic API key
- 可連線的 LanguageTool API，預設使用 `https://api.languagetool.org`

此專案目前沒有額外 Python package dependencies。

## 環境變數

| 變數 | 必填 | 預設值 | 說明 |
| --- | --- | --- | --- |
| `LINE_CHANNEL_SECRET` | LINE webhook 需要 | 空字串 | 驗證 LINE webhook 簽章 |
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE webhook 回覆需要 | 空字串 | 呼叫 LINE reply API |
| `ANTHROPIC_API_KEY` | LLM 建議需要 | 空字串 | 呼叫 Anthropic Messages API |
| `LANGUAGETOOL_API_URL` | 否 | `https://api.languagetool.org` | LanguageTool API base URL |
| `PORT` | 否 | `3000` | HTTP server port |
| `LOG_LEVEL` | 否 | `info` | logger 等級 |
| `LLM_ENABLED` | 否 | `true` | 是否啟用 LLM 批改補充 |
| `LLM_THRESHOLD` | 否 | `70` | LLM 路由門檻設定 |

## 啟動服務

使用 uv 從專案根目錄啟動：

```bash
uv run python server.py
```

啟動後預設監聽：

```text
http://localhost:3000
```

可用端點：

```text
GET  /health
POST /grade
POST /callback
```

## HTTP API 使用

健康檢查：

```bash
curl http://localhost:3000/health
```

批改英文文字：

```bash
curl -X POST http://localhost:3000/grade \
  -H "Content-Type: application/json" \
  -d '{"text":"I go to school yesterday."}'
```

成功回應範例：

```json
{
  "originalText": "I go to school yesterday.",
  "overallScore": 92,
  "source": "nlp+llm",
  "grammar": {
    "score": 85,
    "issues": []
  },
  "spelling": {
    "score": 100,
    "issues": []
  },
  "suggestion": "I went to school yesterday.",
  "tips": "Use past tense for past time expressions."
}
```

輸入限制：

- `text` 必須是字串。
- 不可為空。
- 最多 1000 字元。
- 僅支援英文文字；包含中文會回傳 `400 invalid_text`。

## LINE Webhook 使用

將 LINE Messaging API 的 webhook URL 指到：

```text
https://<your-domain>/callback
```

服務會驗證 `x-line-signature`，簽章不正確會回傳 `401`。

訊息行為：

- 一對一聊天：直接輸入英文句子即可批改。
- 群組或聊天室：需使用 `/check`、`/grade` 或 `/fix` 開頭，例如 `/check I go to school yesterday.`。
- 非文字、太短、網址比例太高、超過 1000 字或包含中文的訊息會被略過或回覆提示。

## 檢查與測試

語法編譯檢查：

```bash
python3 -X pycache_prefix=/private/tmp/chattie_pycache -m compileall .
```

單元測試檔位於 `tests/test_core.py`。目前測試檔使用 top-level imports，但應用程式碼使用 package relative imports；若直接在 `chattie_py/` 目錄執行 `python3 -m unittest discover tests`，會遇到 import path 衝突。修正測試 import 或套件啟動方式後，可使用 unittest 執行測試。
