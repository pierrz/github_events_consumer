"""
Harvests paginated data from the GitHub Events API
"""

import asyncio
import time
from pathlib import Path
from typing import Union

from config import harvester_config
from src.harvester.asyncio_operations import download_github_events, write_aio
from src.harvester.utils import get_events_urls
from worker import celery, logger


@celery.task(name="harvester_task")
def run_harvester() -> Union[int, None]:
    """
    Starts the whole module
    """

    if not harvester_config.DATA_DIR.exists():
        Path.mkdir(harvester_config.DATA_DIR, parents=True)

    try:

        urls = asyncio.run(get_events_urls())
        logger.info(f"Retrieved {len(urls)} event pages")

        start_time = time.time()
        json_data = asyncio.run(download_github_events(urls))
        asyncio.run(write_aio(json_data, harvester_config.DATA_DIR))
        logger.info(f"Downloads took {time.time() - start_time} seconds")

        # send page range as handle to init the cleaning (or not)
        return len(urls)

    except Exception as exception:  # pylint: disable=W0703
        logger.info(exception)
