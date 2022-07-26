"""
Spark jobs module
"""

import os
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

# pylint: disable=E0611
from config import pyspark_config
from src.utils.json_utils import load_json

from .mongo_connectors import DataframeMaker, EventReader


class SparkJobBase(ABC):
    """
    Base class to design actual job from
    """

    flag_files: bool  # to move the files once processed
    input_dir_path = pyspark_config.DATA_DIR
    input_array: Iterable[Dict]

    @abstractmethod
    def __init__(self):
        """
        Triggers the job sequence
        """

    @abstractmethod
    def get_input_array(self):
        """
        Gets the input data
        :return: does its thing
        """

    @abstractmethod
    def process_and_load_data(self):
        """
        Prepares and load data in Mongo
        :return: does its thing
        """


class SparkJobFromJson(SparkJobBase):
    """
    Job meant to process JSON files from a specific directory
    """

    def __init__(self):
        super().__init__()
        json_array, invalid = self.get_input_array()

        if invalid > 0:
            print(f"There were {invalid} invalid or empty files.")

        if len(json_array) > 0:
            self.input_array = json_array
            self.process_and_load_data()
            if self.flag_files:
                self.move_data()
        else:
            print("No data to import.")

    def get_input_array(self) -> Tuple[Iterable[Dict], int]:
        """
        Generate an array containing all new data as separate row per file
        :return: a JSON array and the count of invalid files
        """
        input_array = []
        invalid = 0
        for file in os.scandir(self.input_dir_path):
            data: List = load_json(file)

            if data is not None:
                input_array += data  # /!\ not .append() as data is a list
            else:
                invalid += 1

        return input_array, invalid

    def process_and_load_data(self):
        try:
            print(f"{len(self.input_array)} rows available")
            DataframeMaker(
                self.input_array,
                "event",
                check_columns=["type", "actor_id", "repo_name"],
            ).load_mongo()
            EventReader()
            self.flag_files = True

        except Exception as exception:  # probably some Java error ...      # pylint: disable=W0703
            self.flag_files = False
            print("Error while executing the task ...")
            print(exception)

    def move_data(self):
        """
        Moves the processed files into the 'processed' directory
        :return: does its thing
        """
        for file in os.scandir(self.input_dir_path):
            shutil.move(file.path, Path(pyspark_config.PROCESSED_DIR, file.name))
