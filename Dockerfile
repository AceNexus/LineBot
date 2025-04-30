# 使用官方的 Python 映像
FROM python:3.10-slim

# 設定工作目錄
WORKDIR /app

# 複製 requirements.txt 到容器中
COPY requirements.txt /app/

# 安裝依賴
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式代碼到容器中
COPY . /app/

# 設定環境變數（選擇性）
ENV FLASK_APP=main.py

# 使用 sh -c 解析環境變數
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:$PORT app:app"]