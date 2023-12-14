import os
import logging
import socket
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from flask import Flask
# Import custom modules from the local project
# Import API resources
from . import resources

LOG_FILE_BACKUP_COUNT = 1
LOG_ROTATION = "midnight"

container_id = socket.gethostname()
timestamp = datetime.today().strftime('%Y-%m-%d')


# App factory
def create_app():
    configure_logger()
    # Create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    # App config
    app.config.from_mapping(ROOT_ROUTE='/')

    # App logger
    app.logger.setLevel(os.environ.get('APP_LOG_LEVEL', 'INFO'))

    # Resources
    resources.define_resources(app)

    return app


def configure_logger():
    log_level = os.getenv("APP_LOG_LEVEL", "INFO")
    log_file_path = os.getenv("LOG_DIR", "/home/etdadm/logs/etd_itest")
    formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - ' +
                '[%(filename)s:%(funcName)s:%(lineno)d] - %(message)s')

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger = logging.getLogger('etd_int_tests')
    logger.addHandler(console_handler)
    # Defaults to console logging
    if os.getenv("CONSOLE_LOGGING_ONLY", "true") == "false":
        file_handler = TimedRotatingFileHandler(
            filename=f"{log_file_path}/{container_id}_console_{timestamp}.log",
            when=LOG_ROTATION,
            backupCount=LOG_FILE_BACKUP_COUNT
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    logger.setLevel(log_level)
