import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler

# --------------------------------------------------------------------------
# 📁 Setup Directories & Filenames
# --------------------------------------------------------------------------
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(
    LOG_DIR,
    f"trading_assistant_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.log"
)

# --------------------------------------------------------------------------
# 🎨 Colored Console Formatter
# --------------------------------------------------------------------------
class ColorFormatter(logging.Formatter):
    """Colorized console log output with clean readable structure."""

    COLORS = {
        "DEBUG": "\033[94m",   # Blue
        "INFO": "\033[92m",    # Green
        "WARNING": "\033[93m", # Yellow
        "ERROR": "\033[91m",   # Red
        "CRITICAL": "\033[95m" # Magenta
    }
    RESET = "\033[0m"

    def format(self, record):
        color = self.COLORS.get(record.levelname, "")
        msg = super().format(record)
        return f"{color}{msg}{self.RESET}"

# --------------------------------------------------------------------------
# 🧠 Unified Formatter (for both file & console)
# --------------------------------------------------------------------------
FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

file_formatter = logging.Formatter(FORMAT, datefmt=DATE_FORMAT)
console_formatter = ColorFormatter("[%(levelname)s] %(message)s")

# --------------------------------------------------------------------------
# 💾 Rotating File Handler (max 5MB, keep 5 backups)
# --------------------------------------------------------------------------
file_handler = RotatingFileHandler(
    LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
)
file_handler.setFormatter(file_formatter)
file_handler.setLevel(logging.INFO)

# --------------------------------------------------------------------------
# 🖥️ Console Handler
# --------------------------------------------------------------------------
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(console_formatter)
console_handler.setLevel(logging.INFO)

# --------------------------------------------------------------------------
# 🧩 Configure Logger
# --------------------------------------------------------------------------
logger = logging.getLogger("TradingAssistant")
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(console_handler)
logger.propagate = False  # Prevent duplicate logs

# --------------------------------------------------------------------------
# 🔧 Helper Log Wrappers
# --------------------------------------------------------------------------
def log_info(message: str):
    """Log informational message."""
    try:
        logger.info(message)
    except Exception:
        print(f"[INFO] {message}")

def log_warning(message: str):
    """Log warning message."""
    try:
        logger.warning(message)
    except Exception:
        print(f"[WARN] {message}")

def log_error(message: str):
    """Log error message."""
    try:
        logger.error(message)
    except Exception:
        print(f"[ERROR] {message}")

def log_exception(message: str):
    """Log full stack trace of an exception."""
    try:
        logger.exception(message)
    except Exception:
        print(f"[EXCEPTION] {message}")

# --------------------------------------------------------------------------
# ✅ Test Run Message
# --------------------------------------------------------------------------
log_info("✅ TradingAssistant Logger initialized successfully.")
