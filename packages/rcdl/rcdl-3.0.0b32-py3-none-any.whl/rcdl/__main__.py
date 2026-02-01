# __main__.py

"""
__main__: entry in the programm
Setup logging, create files/folders structures, check dependencies,
init Config global variables, init database,
Then call cli group
"""

import logging

from rcdl.core.config import Config, setup_logging, check_dependencies

# setup file structure
Config.ensure_dirs()
Config.ensure_files()

# load config file settings
Config.load_config()

# setup logging
setup_logging(Config.LOG_FILE, level=0)

# check dependencies
check_dependencies()

logging.info("--- INIT ---")
logging.info("Logger initialized")

# init database
from rcdl.core.db import DB  # noqa: E402

db = DB()
db.init_database()
db.close()

from rcdl.interface.cli import cli  # noqa: E402, F401
