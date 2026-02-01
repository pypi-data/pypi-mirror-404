import logging
from rich.logging import RichHandler

# Configure Root Logger for the Server
logging.basicConfig(
    level="INFO", # or DEBUG
    format="%(message)s",
    datefmt="[%X]",
    handlers=[
        RichHandler(
            show_time=False,      # 🟢 Hides [01/19/26 19:39:27]
            show_path=False,      # 🟢 Hides context.py:792
            show_level=True,
            markup=True
        )
    ]
)

# If FastMCP has already configured a logger, force update its handlers
# (Some libraries verify handlers exist and skip config if so)
fastmcp_logger = logging.getLogger("fastmcp")
fastmcp_logger.handlers = [] # Clear existing
fastmcp_logger.addHandler(
    RichHandler(show_time=False, show_path=False)
)