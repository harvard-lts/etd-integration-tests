import os
import click
import logging
import traceback
from logging.handlers import TimedRotatingFileHandler
from flask import Flask, current_app
# Import custom modules from the local project
# Import API resources
from . import resources

LOG_FILE_BACKUP_COUNT = 1
LOG_ROTATION = "midnight"


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
    log_dir = os.getenv("LOG_DIR", "/home/etdadm/logs/etd_itest")
    log_file_path = os.path.join(log_dir, "int_tests.log")
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    file_handler = TimedRotatingFileHandler(
        filename=log_file_path,
        when=LOG_ROTATION,
        backupCount=LOG_FILE_BACKUP_COUNT
    )

    logger = logging.getLogger('etd_int_tests')
    logger.addHandler(file_handler)
    file_handler.setFormatter(formatter)
    logger.setLevel(log_level)
