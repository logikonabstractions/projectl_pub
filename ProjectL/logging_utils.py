# ProjectL/logging_utils.py
import logging
import os
import datetime
import sys
from logging.handlers import RotatingFileHandler

# Define log levels that match our custom modes
LOG_LEVELS = {
    "normal": logging.INFO,
    "detailed": logging.DEBUG,
    "full_debug": logging.DEBUG  # Same level as detailed, but we'll use custom filters
}


# Custom filter for full debug mode
class FullDebugFilter(logging.Filter):
    def filter(self, record):
        return True  # Allow all records in full debug mode


# Custom filter for detailed mode
class DetailedFilter(logging.Filter):
    def filter(self, record):
        # Filter out some verbose messages that would only be useful in full debug
        if hasattr(record, 'verbose') and record.verbose:
            return False
        return True


# Custom filter for normal mode
class NormalFilter(logging.Filter):
    def filter(self, record):
        # Only allow records with normal=True attribute
        return getattr(record, 'normal', False)


def setup_logging(config):
    """
    Set up logging based on configuration

    Args:
        config: Dictionary containing logging configuration
    """
    # Get logging configuration
    log_config = config.get("logging", {})
    log_mode = log_config.get("mode", "normal").lower()
    log_dir = log_config.get("log_dir", "logs")
    log_name = log_config.get("logger_name", "projectL")
    max_file_size_mb = log_config.get("max_file_size_mb", 5)
    backup_count = log_config.get("backup_count", 3)

    # Create logs directory if it doesn't exist
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Create a unique filename with timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"projectL_{log_mode}_{timestamp}.log")

    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Capture all logs

    # Clear any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')

    # File handler with rotation
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_file_size_mb * 1024 * 1024,
        backupCount=backup_count
    )

    class UnbufferedStreamHandler(logging.StreamHandler):
        def emit(self, record):
            super().emit(record)
            self.flush()

    console_handler = UnbufferedStreamHandler(sys.stdout)

    # # Console handler
    # console_handler = logging.StreamHandler(sys.stdout)

    # Configure based on mode
    if log_mode == "full_debug":
        file_handler.setFormatter(detailed_formatter)
        console_handler.setFormatter(detailed_formatter)
        file_handler.addFilter(FullDebugFilter())
        console_handler.addFilter(FullDebugFilter())
    elif log_mode == "detailed":
        file_handler.setFormatter(detailed_formatter)
        console_handler.setFormatter(detailed_formatter)
        file_handler.addFilter(DetailedFilter())
        console_handler.addFilter(DetailedFilter())
    else:  # normal mode
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        file_handler.addFilter(NormalFilter())
        console_handler.addFilter(NormalFilter())

    # Set levels
    file_handler.setLevel(LOG_LEVELS.get(log_mode, logging.INFO))
    console_handler.setLevel(LOG_LEVELS.get(log_mode, logging.INFO))

    # Add handlers to root logger
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Create a game logger that will be used throughout the application
    game_logger = logging.getLogger(log_name)

    # Log startup information
    game_logger.info("Logging initialized in %s mode", log_mode, extra={"normal": True})
    game_logger.debug("Detailed logging enabled", extra={"normal": False})
    if log_mode == "full_debug":
        game_logger.debug("Full debug mode active - all messages will be logged",
                          extra={"normal": False, "verbose": True})

    return game_logger