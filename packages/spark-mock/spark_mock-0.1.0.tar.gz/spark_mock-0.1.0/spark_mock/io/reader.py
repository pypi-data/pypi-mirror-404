"""
DataFrameReader - reads data from various sources.
"""
from typing import Optional, Dict, List, Union, Any
import polars as pl
from pathlib import Path


class DataFrameReader:
    """
    Interface for reading data into a DataFrame.
    
    Example:
        df = spark.read.csv("data.csv", header=True)
        df = spark.read.format("json").load("data.json")
    """
    
    def __init__(self, spark_session: "SparkSession"):
        self._spark = spark_session
        self._format: Optional[str] = None
        self._schema = None
        self._options: Dict[str, Any] = {}
    
    def format(self, source: str) -> "DataFrameReader":
        """Specify the input data source format."""
        self._format = source.lower()
        return self
    
    def schema(self, schema) -> "DataFrameReader":
        """Specify the input schema."""
        self._schema = schema
        return self
    
    def option(self, key: str, value: Any) -> "DataFrameReader":
        """Add an input option."""
        self._options[key] = value
        return self
    
    def options(self, **opts) -> "DataFrameReader":
        """Add multiple input options."""
        self._options.update(opts)
        return self
    
    def load(self, path: Optional[str] = None, **options) -> "DataFrame":
        """Load data from the specified path."""
        from spark_mock.sql.dataframe import DataFrame
        from spark_mock.core.lazy import OperationType
        
        self._options.update(options)
        
        if path:
            self._options["path"] = path
        
        if self._format == "csv":
            return self.csv(self._options.get("path", ""))
        elif self._format == "json":
            return self.json(self._options.get("path", ""))
        elif self._format == "parquet":
            return self.parquet(self._options.get("path", ""))
        else:
            raise ValueError(f"Unknown format: {self._format}")
    
    def csv(self, path: str, header: bool = True, inferSchema: bool = True,
            sep: str = ",", quote: str = '"', escape: str = "\\",
            nullValue: str = "", encoding: str = "utf-8", **options) -> "DataFrame":
        """Read a CSV file."""
        from spark_mock.sql.dataframe import DataFrame
        from spark_mock.core.lazy import LazyExecutionPlan, OperationType
        
        # Merge with stored options
        opts = {**self._options, **options}
        header = opts.get("header", header)
        inferSchema = opts.get("inferSchema", inferSchema)
        sep = opts.get("sep", opts.get("delimiter", sep))
        
        # Convert header to boolean if string
        if isinstance(header, str):
            header = header.lower() == "true"
        if isinstance(inferSchema, str):
            inferSchema = inferSchema.lower() == "true"
        
        # Read with Polars
        lazy_df = pl.scan_csv(
            path,
            has_header=header,
            separator=sep,
            quote_char=quote,
            null_values=[nullValue] if nullValue else None,
            infer_schema_length=10000 if inferSchema else 0,
        )
        
        # Create execution plan
        plan = LazyExecutionPlan()
        plan.add_operation(OperationType.SCAN_CSV, path=path, header=header)
        
        return DataFrame(lazy_df, self._spark, plan)
    
    def json(self, path: str, **options) -> "DataFrame":
        """Read a JSON file."""
        from spark_mock.sql.dataframe import DataFrame
        from spark_mock.core.lazy import LazyExecutionPlan, OperationType
        
        # Read with Polars
        lazy_df = pl.scan_ndjson(path)
        
        # Create execution plan
        plan = LazyExecutionPlan()
        plan.add_operation(OperationType.SCAN_JSON, path=path)
        
        return DataFrame(lazy_df, self._spark, plan)
    
    def parquet(self, path: str, **options) -> "DataFrame":
        """Read a Parquet file."""
        from spark_mock.sql.dataframe import DataFrame
        from spark_mock.core.lazy import LazyExecutionPlan, OperationType
        
        # Read with Polars
        lazy_df = pl.scan_parquet(path)
        
        # Create execution plan
        plan = LazyExecutionPlan()
        plan.add_operation(OperationType.SCAN_PARQUET, path=path)
        
        return DataFrame(lazy_df, self._spark, plan)
    
    def table(self, tableName: str) -> "DataFrame":
        """Returns the specified table as a DataFrame."""
        return self._spark.table(tableName)
    
    def text(self, path: str) -> "DataFrame":
        """Read a text file."""
        from spark_mock.sql.dataframe import DataFrame
        from spark_mock.core.lazy import LazyExecutionPlan, OperationType
        
        # Read text file as single column
        with open(path, "r") as f:
            lines = f.readlines()
        
        lazy_df = pl.LazyFrame({"value": [line.rstrip("\n") for line in lines]})
        
        plan = LazyExecutionPlan()
        plan.add_operation(OperationType.SCAN_CSV, path=path)
        
        return DataFrame(lazy_df, self._spark, plan)
