# LINE 訊息 Webhook 服務

[![Python 版本](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-2.3.3-brightgreen.svg)](https://flask.palletsprojects.com/)
[![LINE Bot SDK](https://img.shields.io/badge/LINE%20Bot%20SDK-3.5.0-00C300.svg)](https://github.com/line/line-bot-sdk-python)
[![授權條款](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

處理 LINE Messaging API 的 webhook 請求設計。

## 功能特點

- **可靠的 Webhook 處理**：透過簽名驗證機制，安全處理來自 LINE 平台的 webhook 請求
- **訊息處理**：處理並回應 LINE 訊息
- **健康監控**：用於監控服務狀態
- **日誌記錄**：詳細的日誌記錄，便於除錯和監控
- **Docker 支援**：容器化部署，確保跨環境的一致執行
- **環境設定**：透過環境變數提供彈性配置

## 專案架構

```
├── app.py              # 應用程式入口點
├── requirements.txt    # Python 依賴套件
├── Dockerfile          # 容器定義檔
└── .env.example        # 環境變數範本
```

## 部署選項

### 前置需求

- Python 3.11+
- Docker（容器化部署可選）
- LINE 開發者帳號和已設定的 Messaging API 頻道

### 標準部署

1. **Clone 儲存庫**

   ```bash
   git clone https://github.com/yourusername/line-message-webhook.git
   cd line-message-webhook
   ```

2. **設定環境變數**

   ```bash
   cp .env.example .env
   # 編輯 .env 文件，填入您的 LINE 頻道憑證
   ```

3. **安裝依賴套件**

   ```bash
   pip install -r requirements.txt
   ```

4. **啟動服務**
   ```bash
   python app.py
   ```
   服務將在 `http://localhost:8080` 可用

### Docker 部署

1. **建立 Docker 映像檔**

   ```bash
   docker build -t line-message-webhook:latest .
   ```

2. **運行容器**
   ```bash
   docker run -d -p 8080:8080 --env-file .env --name line-webhook line-message-webhook:latest
   ```

## API 端點

| 端點       | 方法 | 說明                                     |
| ---------- | ---- | ---------------------------------------- |
| `/`        | GET  | 服務資訊頁面                             |
| `/health`  | GET  | 用於監控的健康檢查端點                   |
| `/webhook` | POST | LINE 平台 webhook 接收器（需要簽名驗證） |

## 配置參數

| 環境變數                    | 說明              | 預設值 |
| --------------------------- | ----------------- | ------ |
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE 頻道存取令牌 | _必填_ |
| `LINE_CHANNEL_SECRET`       | LINE 頻道密鑰     | _必填_ |
| `PORT`                      | 服務監聽的埠號    | `8080` |
| `LOG_LEVEL`                 | 日誌記錄詳細程度  | `INFO` |
