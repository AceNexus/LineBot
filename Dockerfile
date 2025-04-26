# 使用官方 Python 映像檔
FROM python:3.11-slim

# 設定台北時區
ENV TZ=Asia/Taipei
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && \
    echo $TZ > /etc/timezone && \
    apt-get update && \
    apt-get install -y tzdata && \
    rm -rf /var/lib/apt/lists/*

# 設定工作目錄
WORKDIR /app

# 複製依賴檔案進容器
COPY requirements.txt ./ 

# 安裝依賴
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式檔案進容器
COPY lineMessageNews.py ./

# 預設執行指令
CMD ["python", "lineMessageNews.py"]