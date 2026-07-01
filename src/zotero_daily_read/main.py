import os
import sys
import logging
from omegaconf import DictConfig
import hydra
from loguru import logger
import dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from zotero_daily_read.executor import Executor

os.environ["TOKENIZERS_PARALLELISM"] = "false"
dotenv.load_dotenv()


@hydra.main(version_base=None, config_path="../../config", config_name="default")
def main(config: DictConfig):
    log_level = "DEBUG" if config.executor.debug else "INFO"
    logger.remove()
    logger.add(
        sys.stdout,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )

    for logger_name in logging.root.manager.loggerDict:
        if "zotero_daily_read" in logger_name:
            continue
        logging.getLogger(logger_name).setLevel(logging.WARNING)

    if config.executor.debug:
        logger.info("Debug mode is enabled")

    executor = Executor(config)
    executor.run()


if __name__ == '__main__':
    main()
