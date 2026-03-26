import logging
import os

LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")


def setup_logger():
    os.makedirs(LOG_DIR, exist_ok=True)
    logger = logging.getLogger("sim_trajectoire")
    if not logger.handlers:
        handler = logging.FileHandler(os.path.join(LOG_DIR, "app.log"))
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
        )
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
    return logger
