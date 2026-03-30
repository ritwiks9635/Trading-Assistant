import logging
import os
from datetime import datetime

# --- Create logs directory if it doesn't exist ---
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# --- Configure logging ---
log_file = os.path.join(LOG_DIR, f"trading_assistant_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.log")

logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# --- Custom logger instance ---
logger = logging.getLogger("TradingAssistant")


def log_info(message: str):
    logger.info(message)


def log_warning(message: str):
    logger.warning(message)


def log_error(message: str):
    logger.error(message)


def log_exception(message: str):
    logger.exception(message)


# Optional: Print to console too (for CLI visibility)
class ConsoleHandler(logging.StreamHandler):
    def emit(self, record):
        super().emit(record)
        print(self.format(record))

if not any(isinstance(h, ConsoleHandler) for h in logger.handlers):
    console_handler = ConsoleHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    logger.addHandler(console_handler)
