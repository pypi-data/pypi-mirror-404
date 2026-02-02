import logging
from sys import stdout

def configure_logger(log_level):
    """Configures a logger with the specified name and logger name.
    
    :param name: The name of the app.
    :param logger_name: The name of the logger.
    :return: A configured logger instance.
    """

    # Get the log level from environment variable, default to INFO if not set
    logger = logging.getLogger()
    logger.handlers.clear()

    try:
        # Convert the log level string to an actual logging level
        log_level = getattr(logging, log_level.upper())
        logger.setLevel(log_level)
    except AttributeError:
        # Handle invalid log level
        logger.setLevel(logging.INFO)
        logger.error(f"Invalid log level: {log_level}. Defaulted to INFO.")
    
    # Set the log level
    logger.propagate = False
    
    # Create a stream handler
    stream_handler = logging.StreamHandler(stdout)
    stream_handler.setLevel(log_level)
    
    # Define a simple formatter
    logger.info('Logging Level: %s', logger.level)
    if logger.level <= logging.DEBUG:
        formatter = ColourFormatter(
            "[%(asctime)s %(levelname)s] %(message)s",
            "%H:%M:%S"
        )
    else:
        formatter = ColourFormatter(
            "%(message)s",
            "%H:%M:%S"
        )
    stream_handler.setFormatter(formatter)
    
    # Add the stream handler to the logger
    logger.addHandler(stream_handler)
    
    return logger

class ColourFormatter(logging.Formatter):
    LEVEL_COLOURS = {
        logging.DEBUG: "\033[36m",     # Cyan
        logging.INFO: "\033[32m",      # Green
        logging.WARNING: "\033[33m",   # Yellow
        logging.ERROR: "\033[31m",     # Red
        logging.CRITICAL: "\033[41m",  # Red background
    }
    RESET = "\033[0m"

    def format(self, record):
        levelname = record.levelname
        colour = self.LEVEL_COLOURS.get(record.levelno, "")
        record.levelname = f"{colour}{levelname}{self.RESET}"
        return super().format(record)