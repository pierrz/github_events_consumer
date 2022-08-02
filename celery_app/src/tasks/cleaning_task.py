"""
Cleaning task aka deleting all files in the local 'data/processed' directory and related Mongo collection
"""
import os
import shutil
from pathlib import Path
from typing import List

from config import data_dir_root, diagrams_dir, pyspark_config
from worker import celery, logger


@celery.task(name="cleaning_task")
def clean_local_files(args: List[int], wait_minutes: int):
    """
    Task deleting all the files whose data was already loaded in Mongo
    :return: does its thing
    """

    file_count, page_range = args
    rest_minutes = wait_minutes - int(file_count / page_range)

    if rest_minutes == 0:
        logger.info("Cleaning task initialised ...")
        shutil.rmtree(pyspark_config.PROCESSED_DIR)
        logger.info(f"- {file_count} data files were deleted.")

        templates_dir = Path(data_dir_root, diagrams_dir)
        diag_count = len(os.listdir(templates_dir))
        shutil.rmtree(templates_dir)
        logger.info(f"- {diag_count} HTML diagrams were deleted.")

    else:
        logger.info(
            f"=> {rest_minutes} minutes remaining before next cleaning operation."
        )
