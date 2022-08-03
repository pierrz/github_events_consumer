"""
Mongo connectors
"""
# TODO: refactoring to discard all E1101 errors from pylint (currently ignored)

from abc import ABC
from typing import Dict, Iterable, List

import pandas as pd
from config import pyspark_config
# pylint: disable=E0611
from pyspark.sql import DataFrame
from pyspark.sql import functions as psf
from pyspark.sql.types import StructType

from .runner import spark


class MongoCollection(ABC):
    """
    Base class defining a Mongo table name
    """

    collection: str


class MongoConnector(MongoCollection, ABC):
    """
    Base class extending MongoCollection with columns to check during data processes
    """

    check_columns: Iterable[psf.col]


class DataframeMaker(MongoCollection, ABC):
    """
    Class used to read data and transform it into PySpark dataframe.
    Can also load the produced data into Mongo.
    """

    flat_df: pd.DataFrame
    spark_df: DataFrame
    schema: StructType
    check_columns: Iterable[str] = None

    def __init__(
        self, input_array: Iterable[Dict], collection: str, check_columns=check_columns
    ):
        self.check_columns = check_columns
        self.collection = collection
        self.normalize_input_data(input_array)
        self.prepare_spark_dataframes()

    def normalize_input_data(self, input_array: Iterable[Dict]):
        """
        Takes the input data and clean/normalise it
        :return: does its thing
        """
        print("=> Normalising data ...")
        print(len(input_array))
        flat_df: pd.DataFrame = pd.json_normalize(input_array)
        print("=> ... data normalised.")

        # hack to load Mongo seamlessly
        print("=> Preparing dataframe for Mongo ...")
        columns_to_drop = []
        mapper = {}
        for col in flat_df.columns.to_list():
            if col.startswith("payload.") or col.startswith("org."):
                columns_to_drop.append(col)

            if "." in col:
                mapper[col] = col.replace(".", "_")

        if len(columns_to_drop) > 0:
            flat_df.drop(
                columns=columns_to_drop, inplace=True
            )  # reducing the loaded data (prod)

        flat_df.rename(columns=mapper, inplace=True)

        print(" ... dataframe finalised.")

        columns = flat_df.columns.to_list()
        print(f"with {flat_df.shape[0]} rows and {len(columns)} columns")

        # # extended logs (extra info for celery)
        # print(columns)
        # if self.check_columns is not None:
        #     print(flat_df[self.check_columns])
        self.flat_df = flat_df

    def prepare_spark_dataframes(self):
        """
        Generates the PySpark dataframes from the cleaned/normalised data
        :return: does its thing
        """
        print("=> Preparing PySpark dataframe ...")
        self.spark_df = spark.createDataFrame(data=self.flat_df)
        self.schema = self.spark_df.schema
        # # extended logs (extra info for celery)
        # print("... PySpark dataframe prepared with inferred schema:\n")
        # self.spark_df.printSchema()
        # self.spark_df.select(*self.check_columns).show()

    def load_mongo(self):
        """
        Load mongo with the produced PySpark dataframes
        :return: does its thing
        """
        return MongoLoader(self.spark_df, self.collection)


class MongoLoader(ABC):
    """
    Base class dedicated  to load a specific Mongo collection
    """

    def __init__(self, spark_df: DataFrame, collection: str):
        print("=> Loading Mongo ...")
        spark_df.write.format("mongo").options(
            uri=pyspark_config.MONGODB_URI,
            database=pyspark_config.DB_NAME,
            collection=collection,
        ).mode("append").save()
        print(" ... Mongo loaded")


class MongoReader(ABC):
    """
    Base class dedicated to read data from a specific Mongo collection
    """

    db_data: DataFrame
    schema: StructType
    initial_id_col: List
    columns: Iterable[str]
    n_rows: int

    def __init__(self):

        print("=> Reading Mongo ...")
        db_data = (
            spark.read.format("mongo")
            .option("database", pyspark_config.DB_NAME)
            .option("collection", self.collection)  # pylint: disable=E1101
            .load()
        )

        # preps
        self.n_rows = db_data.count()
        self.columns = list(db_data.columns)
        self.initial_id_col = self.columns[
            1
        ]  # hack to enforce ascending order (test purpose)
        self.db_data = db_data.sort(self.initial_id_col)
        self.schema = self.db_data.schema

        # checks
        print(self.__str__())
        self.db_data.select(*self.check_columns)

    def __str__(self):

        trimmed_cols_str = ""
        for idx, column in enumerate([*self.columns[:3], "...", *self.columns[-3:]]):
            col_str = column
            if idx > 0:
                col_str = f", {col_str}"
            trimmed_cols_str += col_str

        return (
            f"Spark dataframe from Mongo collection '{self.collection}' "  # pylint: disable=E1101
            f"with {self.db_data.count()} rows and {len(self.columns)} columns [{trimmed_cols_str}]"
        )

    def __repr__(self):
        # pylint: disable=E1101
        return f"MongoReader('{self.collection}' collection, {len(self.columns)} columns, {self.db_data.count()} rows)"


class EventBase(MongoConnector, ABC):
    """
    Base class dedicated to defining the Mongo collection 'character' related to the Marvel Characters API data
    """

    collection = "event"
    check_columns = [
        psf.col("id"),
        psf.col("type"),
        psf.col("actor_id"),
        psf.col("repo_name"),
    ]


class EventLoader(EventBase, MongoLoader):
    """
    Class dedicated to load the Mongo collection 'event' with new data
    """


class EventReader(EventBase, MongoReader):
    """
    Class dedicated to read data from the Mongo collection 'event'
    """
