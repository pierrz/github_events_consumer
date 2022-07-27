"""
Cleaning task aka deleting all files in the local 'data/processed' directory and related Mongo collection
"""

import shutil

from config import pyspark_config
from worker import celery, logger


@celery.task(name="cleaning_task")
def clean_local_files(args, wait_minutes):
    """
    Task deleting all the files whose data was already loaded in Mongo
    :return: does its thing
    """
    logger.info("Cleaning task initialised ...")
    # if init_flag:
    file_count, page_range = args
    if file_count >= page_range * wait_minutes:

        shutil.rmtree(pyspark_config.PROCESSED_DIR)
        logger.info("All processed data files were deleted.")

    else:
        logger.info("No data files to delete.")
