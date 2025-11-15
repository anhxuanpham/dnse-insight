"""
Logging configuration using Loguru
"""
import sys
from pathlib import Path
from loguru import logger
from utils.config import settings


def setup_logger():
    """Setup logger with file and console handlers"""

    # Remove default handler
    logger.remove()

    # Create logs directory if it doesn't exist
    log_path = Path(settings.log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Console handler
    logger.add(
        sys.stdout,
        colorize=True,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.log_level,
    )

    # File handler - main log
    logger.add(
        settings.log_file,
        rotation="500 MB",
        retention="30 days",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=settings.log_level,
    )

    # File handler - error log
    error_log_file = log_path.parent / "error.log"
    logger.add(
        str(error_log_file),
        rotation="100 MB",
        retention="90 days",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
    )

    # File handler - trading log (for audit trail)
    trading_log_file = log_path.parent / "trading.log"
    logger.add(
        str(trading_log_file),
        rotation="1 day",
        retention="365 days",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {message}",
        level="INFO",
        filter=lambda record: "TRADE" in record["extra"],
    )

    return logger


# Initialize logger
setup_logger()
