import logging


def setup_logger(app):
    log_level = app.config.get('LOG_LEVEL', 'INFO').upper()

    if log_level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
        log_level = 'INFO'

    # 設置 root logger 的格式與等級
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=getattr(logging, log_level)
    )

    # 設置 Flask logger 的等級
    app.logger.setLevel(log_level)

    # 防止重複輸出
    app.logger.propagate = False
