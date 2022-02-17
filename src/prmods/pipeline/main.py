import logging
from os import environ

from prmods.pipeline.config import OdsPortalConfig
from prmods.pipeline.ods_downloader import OdsDownloader
from prmods.utils.io.json_formatter import JsonFormatter

logger = logging.getLogger("prmods")


def _setup_logger():
    logger.setLevel(logging.INFO)
    formatter = JsonFormatter()
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def main():
    _setup_logger()
    config = OdsPortalConfig.from_environment_variables(environ)
    OdsDownloader(config).run()


if __name__ == "__main__":
    main()
