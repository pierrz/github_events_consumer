"""
Loads required data from JSON files into MongoDB
"""

import os

from config import pyspark_config
from src.pyspark.jobs import SparkJobFromJson
from worker import celery, logger


@celery.task(name="pyspark_task")
def run_pyspark(page_range):
    """
    Starts the whole module
    *args is bein used to handle the 'None' returned by harvester_task (necessary for the scheduled chain)
    """

    if not pyspark_config.PROCESSED_DIR.exists():
        os.mkdir(pyspark_config.PROCESSED_DIR)

    logger.info("Initiating data loading task to Mongo ...")
    SparkJobFromJson()
    logger.info("=> Data loaded successfully.")

    # init or not the cleaning
    wait_minutes = 2
    if len(os.listdir(pyspark_config.PROCESSED_DIR)) >= page_range * wait_minutes:
        return True
    return False
