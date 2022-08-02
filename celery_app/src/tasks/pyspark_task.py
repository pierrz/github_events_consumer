"""
Loads required data from JSON files into MongoDB
"""

import os
from pathlib import Path
from typing import List

from config import pyspark_config
from src.pyspark.jobs import SparkJobFromJson
from worker import celery, logger


@celery.task(name="pyspark_task")
def run_pyspark(page_range: int) -> List[int]:
    """
    Starts the whole module
    *args is bein used to handle the 'None' returned by harvester_task (necessary for the scheduled chain)
    """

    if not pyspark_config.PROCESSED_DIR.exists():
        Path.mkdir(pyspark_config.PROCESSED_DIR, parents=True)

    logger.info("Initiating data loading task to Mongo ...")
    SparkJobFromJson()
    logger.info("=> Data loaded successfully.")

    file_count = len(os.listdir(pyspark_config.PROCESSED_DIR))
    if file_count is None:
        return [0, page_range]
    return [file_count, page_range]
