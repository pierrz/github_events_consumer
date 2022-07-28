"""
Cleaning task aka deleting all files in the local 'data/processed' directory and related Mongo collection
"""

import shutil
from typing import List

from config import pyspark_config
from worker import celery, logger


@celery.task(name="cleaning_task")
def clean_local_files(args: List[int], wait_minutes: int):
    """
    Task deleting all the files whose data was already loaded in Mongo
    :return: does its thing
    """

    file_count, page_range = args
    threshold = page_range * wait_minutes

    if file_count >= threshold:

        logger.info("Cleaning task initialised ...")
        shutil.rmtree(pyspark_config.PROCESSED_DIR)
        logger.info(f"{file_count} files were deleted.")

    else:
        rest = (threshold - file_count) / page_range
        logger.info(f"=> {int(rest)} minutes remaining before next cleaning operation.")
