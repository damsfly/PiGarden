import logging
import os


def setup_logger(log_file_name, logger_name=None):
    # Get the absolute path to the directory where this script is located
    script_dir = os.path.dirname(os.path.realpath(__file__))

    # Combine the script directory with the relative path to form an absolute path to the log file
    log_path = os.path.join(script_dir, log_file_name)

    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)

    # Formatter for the logs
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # File handler
    file_handler = logging.FileHandler(log_path)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Stream handler for console output (optional)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    # Setting log level for requests and urllib3 to WARNING to avoid DEBUG messages
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    return logger

