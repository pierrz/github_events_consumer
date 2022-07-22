"""
Loads required data from JSON files into MongoDB
"""

import os
from datetime import datetime, timezone

from config import pyspark_config
from src.db.mongo import init_db_connection
from src.pyspark.jobs import SparkJobFromJson
from worker import celery, logger


@celery.task(name="pyspark_task", bind=True)
def run_pyspark(self):

    if not pyspark_config.PROCESSED_DIR.exists():
        os.mkdir(pyspark_config.PROCESSED_DIR)

    current_id = self.request.id.__str__()
    row_data = {"task_id": current_id, "created_at": datetime.now(timezone.utc).isoformat()}
    db = init_db_connection()
    db[pyspark_config.TASKID_COLLECTION].insert_one(row_data)  # storing the current task uuid in Mongo

    logger.info("Initiating data loading task to Mongo ...")
    SparkJobFromJson()
    logger.info("=> Data loaded successfully.")

    # shutil.rmtree(pyspark_config.PROCESSED_DIR)
    # logger.info("All processed data files were deleted.")
