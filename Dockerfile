# 使用官方內建瀏覽器的 Playwright Python 映像
FROM mcr.microsoft.com/playwright/python:v1.52.0-jammy

# 設定工作目錄
WORKDIR /app

# 複製 requirements.txt 並安裝 Python 依賴
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式碼
COPY . /app/

# 設定環境變數（選擇性）
ENV FLASK_APP=main.py

# 啟動應用程式
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:$PORT main:app"]
