import logging
from rich.logging import RichHandler

def setup_logger(name="fractale", quiet=False, debug=True):
    """
    Configures a clean logger without timestamps or file paths.
    """
    # Create the handler with specific display options turned off
    handler = RichHandler(
        show_time=not quiet,
        show_path=debug,
        show_level=True, 
        markup=True,    
        rich_tracebacks=True
    )
    
    # Set the format to JUST the message (Rich adds the level/color automatically)
    formatter = logging.Formatter("%(message)s")
    handler.setFormatter(formatter)

    # Configure the root logger or specific logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Remove default handlers to prevent duplicates
    if logger.hasHandlers():
        logger.handlers.clear()
        
    logger.addHandler(handler)
    return logger

# Initialize immediately
logger = setup_logger()
