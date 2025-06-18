FROM mcr.microsoft.com/playwright/python:v1.52.0-jammy

# 設定時區
ENV TZ=Asia/Taipei
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 設定工作目錄
WORKDIR /app

# 安裝 Python 依賴
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製程式碼
COPY . /app/

# 設定環境變數
ENV FLASK_APP=main.py
ENV PORT=5000

# 啟動應用程式
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:$PORT main:app"]
