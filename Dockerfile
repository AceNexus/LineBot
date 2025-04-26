# 使用官方 Python 映像檔
FROM python:3.11-slim

# 設定工作目錄
WORKDIR /app

# 設定環境變數
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 複製依賴檔案進容器
COPY requirements.txt ./

# 安裝依賴
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式檔案進容器
COPY app.py ./
COPY .env ./.env

# 暴露應用程式端口
EXPOSE 8080

# 使用 gunicorn 啟動應用
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]