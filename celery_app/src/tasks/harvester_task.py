"""
Harvests paginated data from the GitHub Events API
"""

import asyncio
import os
import time

from config import harvester_config
from src.harvester.asyncio_operations import download_aio, write_aio
from src.harvester.utils import get_events_urls
from worker import celery, logger


@celery.task(name="harvester_task")
def run_harvester():
    """
    Starts the whole module
    """

    if not harvester_config.DATA_DIR.exists():
        os.mkdir(harvester_config.DATA_DIR)

    try:

        urls = get_events_urls()

        logger.info(f"Retrieved {len(urls)} event pages")
        start_time = time.time()
        json_data = asyncio.run(download_aio(urls))
        asyncio.run(write_aio(json_data, harvester_config.DATA_DIR))
        logger.info(f"Downloads took {time.time() - start_time} seconds")

        # send page range as handle to init the cleaning (or not)
        return len(urls)

    except Exception as exception:  # pylint: disable=W0703
        logger.info(exception)
