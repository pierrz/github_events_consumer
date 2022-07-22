"""
Cleaning task aka deleting all files in the local 'data/processed' directory and related Mongo collection
"""

import shutil

from celery.result import AsyncResult
from config import pyspark_config
from src.db.mongo import init_db_connection
from worker import celery, logger


def check_last_task_status(db):
    row = db[pyspark_config.TASKID_COLLECTION].find().sort("created_at", -1).limit(1)
    row_list = list(row)
    last_row = row_list[0]
    last_task_id = last_row["task_id"]

    # proceeds only if last pyspark-mongo task finished
    last_task = AsyncResult(last_task_id)
    is_task_ready = last_task.ready()
    print(is_task_ready)
    while not is_task_ready:
        is_task_ready = last_task.ready()
    print(is_task_ready)


@celery.task(name="cleaning_task")
def cleaning_task():
    """
    Task deleting all the files whose data was already loaded in Mongo
    :return: does its thing
    """
    logger.info("Cleaning task initialised ...")
    if pyspark_config.PROCESSED_DIR.exists():

        db = init_db_connection()
        check_last_task_status(db)

        shutil.rmtree(pyspark_config.PROCESSED_DIR)
        logger.info("All processed data files were deleted.")

        db.drop_collection(pyspark_config.TASKID_COLLECTION)
        logger.info(f"'{pyspark_config.TASKID_COLLECTION}' deleted in Mongo.")

    else:
        logger.info("No data files to delete.")
