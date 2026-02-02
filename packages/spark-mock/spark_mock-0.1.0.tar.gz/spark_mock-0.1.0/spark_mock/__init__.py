"""
Spark Mock Framework
A mock Apache Spark framework powered by Polars for learning purposes.
"""

__version__ = "0.1.0"

from spark_mock.sql.session import SparkSession
from spark_mock.sql.dataframe import DataFrame
from spark_mock.sql.column import Column
from spark_mock.sql import functions
from spark_mock.sql import types

__all__ = [
    "SparkSession",
    "DataFrame",
    "Column",
    "functions",
    "types",
]
