from app import create_app

# 創建 Flask 應用
app = create_app()

# 在生產環境中不需要 if __name__ == '__main__'，因為 Gunicorn 會自動加載這個模塊
