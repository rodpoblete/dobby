import sys
from pathlib import Path
from loguru import logger

def setup_logger(verbose: bool = False, log_file: Path | None = None):
    """
    Configure application logger.
    
    Args:
        verbose: If True, show DEBUG logs. If False, show INFO+ only
        log_file: Optional path to save logs to file
    """
    logger.remove()
    
    log_level = "DEBUG" if verbose else "INFO"
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level=log_level,
        colorize=True,
    )
    
    if log_file:
        logger.add(
            log_file,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
            level="DEBUG",
            rotation="10 MB",
            retention="1 week",
            compression="zip",
        )
    
    return logger
