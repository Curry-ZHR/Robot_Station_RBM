import logging
import sys
from datetime import datetime
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
LOG_DIR = ROOT_DIR / "logs"

SUCCESS_LEVEL = 25
logging.addLevelName(SUCCESS_LEVEL, "SUCCESS")


class RobotLogger(logging.Logger):
    def success(self, message, *args, **kwargs):
        if self.isEnabledFor(SUCCESS_LEVEL):
            self._log(SUCCESS_LEVEL, message, args, **kwargs)


class ColorFormatter(logging.Formatter):
    COLORS = {
        "SUCCESS": "\033[32m",
        "INFO": "\033[36m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[35m",
    }
    RESET = "\033[0m"

    def format(self, record):
        rendered = super().format(record)
        color = self.COLORS.get(record.levelname, "")
        if not color:
            return rendered
        return f"{color}{rendered}{self.RESET}"


_configured = False
_log_file = None


def _timestamped_log_file():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    return LOG_DIR / f"{timestamp}.log"


def setup_logger(name="robot_station"):
    global _configured, _log_file

    logging.setLoggerClass(RobotLogger)
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if _configured:
        return logger

    _log_file = _timestamped_log_file()
    plain_format = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    color_format = ColorFormatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    file_handler = logging.FileHandler(_log_file, encoding="utf-8")
    file_handler.setFormatter(plain_format)
    file_handler.setLevel(logging.INFO)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(color_format)
    stream_handler.setLevel(logging.INFO)

    logger.handlers.clear()
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    _configured = True

    logger.info("Logger initialized: %s", _log_file)
    return logger


def get_logger(name="robot_station"):
    if not _configured:
        return setup_logger(name)
    return logging.getLogger(name)

