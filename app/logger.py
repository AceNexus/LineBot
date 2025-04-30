import logging


def setup_logger(app):
    log_level = app.config.get('LOG_LEVEL', 'INFO').upper()

    if log_level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
        log_level = 'INFO'  # 預設為 INFO 等級

    # 設置日誌格式
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=getattr(logging, log_level)
    )
    app.logger.setLevel(log_level)  # 設定 Flask 的日誌等級
