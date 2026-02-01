import sys
from loguru import logger
from .config import settings

def setup_logger(level: str = None, log_file: str = None):
    # Remove default handler
    logger.remove()
    
    level = level or settings.log.level
    log_file = log_file or settings.log.file
    
    # Add console handler
    logger.add(sys.stderr, level=level, colorize=True, 
               format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")
    
    # Add file handler if specified
    if log_file:
        logger.add(log_file, 
                   level=level, 
                   rotation=settings.log.rotation, 
                   retention=settings.log.retention,
                   compression="zip")

def redact_name(name: str) -> str:
    if not settings.log.redact_names or not name:
        return name
    if len(name) <= 1:
        return "*"
    return name[0] + "*" * (len(name) - 1)

# Initialize with default settings
setup_logger()
