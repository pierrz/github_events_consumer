"""
Configuration module
"""

import os
from pathlib import Path

from celery.schedules import crontab
from pydantic import BaseSettings
from celery import signature


data_dir_root = Path(os.sep, "opt", "data")
data_pipeline_queue = {"queue": "data_pipeline"}


class CeleryConfig(BaseSettings):
    """
    Config class.
    """

    broker_url = os.getenv("CELERY_BROKER_URL")
    result_backend = os.getenv("CELERY_RESULT_BACKEND")
    imports = [
        "src.tasks.test_task",
        "src.tasks.harvester_task",
        "src.tasks.pyspark_task",
        "src.tasks.cleaning_task"
    ]
    enable_utc = True
    timezone = "Europe/Amsterdam"
    task_track_started = True
    result_persistent = True
    task_publish_retry = True
    # The acks_late setting would be used when you need the task to be executed again
    # if the worker (for some reason) crashes mid-execution
    task_acks_late = "Enabled"

    beat_schedule = {
        # TODO: implement that task separately, only in celery_test
        # 'init-test-task': {'task': 'dummy_task', 'schedule': crontab(minute='*'), 'args': [3]},
        'chain': {
            'task': 'harvester_task',
            'schedule': crontab(minute='*'),
            'options': {
                # **data_pipeline_queue,
                **data_pipeline_queue,
                'link': signature('pyspark_task', options=data_pipeline_queue)
                                  # options=data_pipeline_queue)}
            #                       {**data_pipeline_queue,
            #                                'link': signature('cleaning_task',
            #                                                  options=data_pipeline_queue)})
            }
        },

        # 'chain': {
        #     'task': 'harvester_task',
        #     'schedule': crontab(minute='*'),
        #     'options': {
        #         'queue': 'data_pipeline',
        #         'link': signature('pyspark_task', options={'queue': 'data_pipeline'})
        #     }
        # }

        "cleaning-task": {"task": "cleaning_task", "schedule": crontab(minute="*/2"), "options": data_pipeline_queue}
    }


class HarvesterConfig(BaseSettings):
    """
    Harvester module config
    """

    DATA_DIR = Path(data_dir_root, "events")


class PySparkConfig(HarvesterConfig):
    """
    PySpark module config
    """

    MONGODB_URI: str = os.getenv("MONGODB_URI")
    DB_NAME = os.getenv("DB_NAME")
    TASKID_COLLECTION = "taskid"
    PROCESSED_DIR = Path(data_dir_root, "processed")


harvester_config = HarvesterConfig()
celery_config = CeleryConfig()
pyspark_config = PySparkConfig()
