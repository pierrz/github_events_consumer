"""
Loads required data from JSON files into MongoDB
"""

import os
import shutil

from config import pyspark_config
from src.pyspark.jobs import SparkJobFromJson
from worker import celery, logger


@celery.task(name="pyspark_task")
def run_pyspark():

    if not pyspark_config.PROCESSED_DIR.exists():
        os.mkdir(pyspark_config.PROCESSED_DIR)

    logger.info("Initiating data loading task to Mongo ...")
    SparkJobFromJson()
    logger.info("=> Data loaded successfully.")

    # TODO: implement the 'cleaning_task' instead (see related branch)
    shutil.rmtree(pyspark_config.PROCESSED_DIR)
    logger.info("All processed data files were deleted.")
