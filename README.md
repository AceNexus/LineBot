# LINE 訊息 Webhook 服務

[![Python 版本](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-2.3.3-brightgreen.svg)](https://flask.palletsprojects.com/)
[![LINE Bot SDK](https://img.shields.io/badge/LINE%20Bot%20SDK-3.5.0-00C300.svg)](https://github.com/line/line-bot-sdk-python)
[![授權條款](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

處理 LINE Messaging API 的 webhook 請求設計。

## 功能特點

- **可靠的 Webhook 處理**：透過簽名驗證機制，安全處理來自 LINE 平台的 webhook 請求。
- **訊息處理**：處理並回應 LINE 訊息，包括文字、圖片等多種格式。
- **健康監控**：用於監控服務狀態，確保服務正常運作。
- **日誌記錄**：詳細的日誌記錄，便於除錯和監控。
- **Docker 支援**：容器化部署，確保跨環境的一致執行。
- **環境設定**：透過環境變數提供彈性配置。

## 專案架構

```
linemessagewebhook/
├── app/                                 # 主應用程式目錄
│   ├── api/                             # API 相關程式碼
│   │   ├── v1/                          # API v1 版本的路由
│   │   │   ├── __init__.py              # v1 初始化
│   │   │   └── routes.py                # API v1 路由定義
│   │   └── __init__.py                  # api 初始化
│   ├── handlers/                        # 處理外部 webhook、通知等
│   │   ├── __init__.py
│   │   └── line_message_handlers.py     # 處理 LINE Webhook 請求
│   ├── models/                          # 資料模型定義
│   │   └── __init__.py
│   ├── services/                        # 商業邏輯與外部服務整合
│   │   ├── __init__.py
│   │   └── groq_service.py              # Groq API 整合邏輯封裝
│   ├── utils/                           # 工具函式（輔助性功能）
│   │   ├── news.py                      # 取得新聞相關工具
│   │   └── __init__.py
│   ├── __init__.py
│   ├── config.py                        # 設定檔（例如環境變數存取）
│   ├── extensions.py                    # 擴充模組初始化（DB、快取等）
│   └── logger.py                        # 日誌設定
├── migrations/                          # 資料庫遷移檔案
├── tests/                               # 單元測試程式碼
│   └── __init__.py
├── .env                                 # 儲存環境變數
├── .gitignore                           # Git 忽略規則
├── main.py                              # 主應用程式入口
├── Dockerfile                           # Docker 建置設定
├── README.md                            # 專案說明文件
├── requirements.txt                     # 套件安裝需求清單
└── wsgi.py                              # WSGI 啟動器，供 Gunicorn 使用
```

## 部署選項

### 前置需求

- Python 3.11+
- Docker（容器化部署可選）
- LINE 開發者帳號和已設定的 Messaging API 頻道

### 標準部署

1. **Clone 儲存庫**

   ```bash
   git clone https://github.com/AceNexus/AceLineBot.git
   cd line_message_webhook
   ```

2. **設定環境變數**

   ```bash
   nano .env
   ```

   > 確保在 `.env` 文件中設定正確的環境變數，特別是必填項。

3. **安裝依賴套件**

   ```bash
   pip install -r requirements.txt
   ```

   > 確認所有依賴已正確安裝，避免運行時錯誤。

4. **啟動服務**

   ```bash
   python main.py
   ```

   此時服務將在 `http://localhost:{PORT}` 可用，根據 `.env` 文件中設定的 `PORT` 變數（例如 5000）來訪問。

### Docker 部署

1. **Clone 儲存庫**

   ```bash
   git clone git@github.com:AceNexus/AceLineBot.git
   cd AceLineBot
   ```

2. **設定環境變數**

   ```bash
   nano .env
   ```

   > 確保在 `.env` 文件中設定正確的環境變數，特別是必填項。

3. **建立 Docker 映像檔**

   ```bash
   docker build -t acelinebot .
   ```

4. **運行容器**
   在運行容器之前，請確保 `.env` 文件中的 `PORT` 變數與以下命令中的端口一致。

   ```bash
   docker run -d -p 5000:5000 --name acelinebot acelinebot
   ```

5. **確認狀態**

   ```bash
   docker logs -f --tail 1000 acelinebot
   ```

   > 使用此命令可以查看容器的運行日誌，幫助排查問題。

6. **容器已存在，重新建構並運行容器**

   ```bash
   docker rm -f acelinebot 2>/dev/null &&
   docker build -t acelinebot . &&
   docker run --env-file .env -d -p 5000:5000 --name acelinebot acelinebot
   docker logs -f --tail 1000 acelinebot
   ```

## API 端點

| 端點         | 方法   | 說明                          |
|------------|------|-----------------------------|
| `/`        | GET  | 服務資訊頁面                      |
| `/health`  | GET  | 用於監控的健康檢查端點                 |
| `/webhook` | POST | LINE 平台 webhook 接收器（需要簽名驗證） |

## 配置參數

| 環境變數                        | 說明          | 預設值    |
|-----------------------------|-------------|--------|
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE 頻道存取令牌 | _必填_   |
| `LINE_CHANNEL_SECRET`       | LINE 頻道密鑰   | _必填_   |
| `PORT`                      | 服務監聽的埠號     | `5000` |
| `LOG_LEVEL`                 | 日誌記錄詳細程度    | `INFO` |

## 常見問題

1. **啟動服務失敗？**

    - 請檢查是否已正確安裝所有依賴套件（如：Flask、line-bot-sdk、python-dotenv 等）。

2. **收到 401 錯誤？**
    - 請確認環境變數 `LINE_CHANNEL_ACCESS_TOKEN` 和 `LINE_CHANNEL_SECRET` 是否設定正確，並且與 LINE Developers 後台設定一致。
