"""
SparkSession - the entry point for Spark Mock functionality.
"""
from typing import Any, Dict, List, Optional, Union, Tuple
import polars as pl

from spark_mock.sql.types import StructType, StructField, _infer_schema
from spark_mock.sql.catalog import Catalog
from spark_mock.core.execution import ExecutionEngine
from spark_mock.core.partition import PartitionManager
from spark_mock.ui.console import SparkUI


class SparkConf:
    """Configuration for SparkSession."""
    
    def __init__(self):
        self._conf: Dict[str, Any] = {}
    
    def set(self, key: str, value: Any) -> "SparkConf":
        self._conf[key] = value
        return self
    
    def get(self, key: str, defaultValue: Any = None) -> Any:
        return self._conf.get(key, defaultValue)
    
    def setAll(self, pairs: List[Tuple[str, Any]]) -> "SparkConf":
        for k, v in pairs:
            self._conf[k] = v
        return self
    
    def getAll(self) -> List[Tuple[str, Any]]:
        return list(self._conf.items())
    
    def setAppName(self, name: str) -> "SparkConf":
        return self.set("spark.app.name", name)
    
    def setMaster(self, master: str) -> "SparkConf":
        return self.set("spark.master", master)


class SparkContext:
    """Context for Spark Mock."""
    
    _active_context: Optional["SparkContext"] = None
    
    def __init__(self, conf: Optional[SparkConf] = None):
        self._conf = conf or SparkConf()
        self._stopped = False
        SparkContext._active_context = self
    
    @classmethod
    def getOrCreate(cls, conf: Optional[SparkConf] = None) -> "SparkContext":
        if cls._active_context is not None:
            return cls._active_context
        return cls(conf)
    
    @property
    def defaultParallelism(self) -> int:
        return int(self._conf.get("spark.default.parallelism", 4))
    
    @property
    def applicationId(self) -> str:
        return "local-spark-mock"
    
    @property
    def appName(self) -> str:
        return self._conf.get("spark.app.name", "SparkMockApp")
    
    def stop(self):
        self._stopped = True
        SparkContext._active_context = None


class SparkSessionBuilder:
    """Builder for SparkSession."""
    
    def __init__(self):
        self._conf = SparkConf()
    
    def appName(self, name: str) -> "SparkSessionBuilder":
        self._conf.setAppName(name)
        return self
    
    def master(self, master: str) -> "SparkSessionBuilder":
        self._conf.setMaster(master)
        return self
    
    def config(self, key: str = None, value: Any = None, 
               conf: SparkConf = None, **kwargs) -> "SparkSessionBuilder":
        if conf:
            for k, v in conf.getAll():
                self._conf.set(k, v)
        if key and value is not None:
            self._conf.set(key, value)
        for k, v in kwargs.items():
            self._conf.set(k, v)
        return self
    
    def enableHiveSupport(self) -> "SparkSessionBuilder":
        self._conf.set("spark.sql.catalogImplementation", "hive")
        return self
    
    def getOrCreate(self) -> "SparkSession":
        if SparkSession._active_session is not None:
            return SparkSession._active_session
        return SparkSession(self._conf)


class SparkSession:
    """
    The entry point for Spark Mock functionality.
    
    Example:
        spark = SparkSession.builder \\
            .appName("MyApp") \\
            .config("spark.mock.partitions", 4) \\
            .config("spark.mock.ui.html", "true") \\
            .getOrCreate()
    """
    
    _active_session: Optional["SparkSession"] = None
    builder = SparkSessionBuilder()
    
    def __init__(self, conf: Optional[SparkConf] = None):
        self._conf = conf or SparkConf()
        self._sc = SparkContext.getOrCreate(self._conf)
        
        # Get configuration
        self._app_name = self._conf.get("spark.app.name", "SparkMockApp")
        self._num_partitions = int(self._conf.get("spark.mock.partitions", 
                                                   self._conf.get("spark.default.parallelism", 4)))
        self._console_ui_enabled = self._conf.get("spark.mock.ui.console", "true").lower() == "true"
        self._html_ui_enabled = self._conf.get("spark.mock.ui.html", "false").lower() == "true"
        
        # Initialize components
        self._execution_engine = ExecutionEngine(
            num_partitions=self._num_partitions,
            app_name=self._app_name
        )
        self._catalog = Catalog(self)
        
        # Console UI
        self._console_ui = SparkUI(app_name=self._app_name, enabled=self._console_ui_enabled)
        
        # HTML UI
        self._html_ui = None
        if self._html_ui_enabled:
            from spark_mock.ui.html_ui import SparkUIGenerator
            self._html_ui = SparkUIGenerator(app_name=self._app_name)
        
        # Set UI callbacks
        self._execution_engine.set_ui_callback(self._on_job_update)
        
        SparkSession._active_session = self
    
    def _on_job_update(self, job_metrics):
        """Callback for job updates."""
        from spark_mock.core.execution import JobMetrics
        
        # Update console UI
        if self._console_ui_enabled:
            self._console_ui.display_job(job_metrics)
        
        # Update HTML UI
        if self._html_ui and job_metrics:
            job_id = job_metrics.job_id
            status = job_metrics.status.upper()
            
            if status == "RUNNING" and not hasattr(self, f"_job_{job_id}_started"):
                setattr(self, f"_job_{job_id}_started", True)
                self._html_ui.start_job(f"Job {job_id}", num_stages=len(job_metrics.stages))
                for i, stage in enumerate(job_metrics.stages):
                    self._html_ui.add_stage(f"Stage {i}", num_tasks=self._num_partitions)
            
            if status == "COMPLETED":
                # Complete all stages
                for stage in self._html_ui.stages:
                    if stage.status == "RUNNING":
                        metrics = {
                            "input_records": job_metrics.input_rows,
                            "output_records": job_metrics.output_rows,
                            "shuffle_read_bytes": job_metrics.shuffle_stats.shuffle_read_bytes,
                            "shuffle_write_bytes": job_metrics.shuffle_stats.shuffle_write_bytes,
                        }
                        self._html_ui.complete_stage(stage.stage_id, metrics)
                
                self._html_ui.complete_job(job_id, "SUCCEEDED")
    
    @classmethod
    def getActiveSession(cls) -> Optional["SparkSession"]:
        """Returns the active SparkSession."""
        return cls._active_session
    
    @classmethod  
    def getOrCreate(cls) -> "SparkSession":
        """Get or create a SparkSession."""
        if cls._active_session is not None:
            return cls._active_session
        return cls()
    
    @property
    def sparkContext(self) -> SparkContext:
        """Returns the SparkContext."""
        return self._sc
    
    @property
    def catalog(self) -> Catalog:
        """Returns the catalog."""
        return self._catalog
    
    @property
    def conf(self) -> SparkConf:
        """Returns the configuration."""
        return self._conf
    
    @property
    def ui(self) -> Optional["SparkUIGenerator"]:
        """Returns the HTML UI generator if enabled."""
        return self._html_ui
    
    @property
    def read(self) -> "DataFrameReader":
        """Returns a DataFrameReader."""
        from spark_mock.io.reader import DataFrameReader
        return DataFrameReader(self)
    
    @property
    def version(self) -> str:
        """Returns the version."""
        return "spark-mock-0.1.0"
    
    def createDataFrame(
        self, 
        data: Union[List[tuple], List[dict], pl.DataFrame], 
        schema: Union[StructType, List[str], None] = None
    ) -> "DataFrame":
        """
        Create a DataFrame from data.
        
        Args:
            data: List of tuples, list of dicts, or Polars DataFrame
            schema: Schema as StructType or list of column names
        """
        from spark_mock.sql.dataframe import DataFrame
        from spark_mock.core.lazy import LazyExecutionPlan, OperationType
        
        # Handle Polars DataFrame input
        if isinstance(data, pl.DataFrame):
            lazy_df = data.lazy()
            plan = LazyExecutionPlan()
            plan.add_operation(OperationType.CREATE_DATAFRAME, num_rows=len(data))
            return DataFrame(lazy_df, self, plan)
        
        # Handle list of dicts
        if data and isinstance(data[0], dict):
            if schema is None:
                columns = list(data[0].keys())
            elif isinstance(schema, list):
                columns = schema
            else:
                columns = schema.names
            
            rows = [tuple(d.get(c) for c in columns) for d in data]
            data = rows
        else:
            if schema is None:
                raise ValueError("Schema must be provided for tuple data")
            elif isinstance(schema, list):
                columns = schema
            else:
                columns = schema.names
        
        # Create Polars DataFrame
        if not data:
            df_data = {col: [] for col in columns}
        else:
            df_data = {col: [row[i] for row in data] for i, col in enumerate(columns)}
        
        polars_df = pl.DataFrame(df_data)
        lazy_df = polars_df.lazy()
        
        # Create execution plan
        plan = LazyExecutionPlan()
        plan.add_operation(OperationType.CREATE_DATAFRAME, num_rows=len(data) if data else 0)
        
        return DataFrame(lazy_df, self, plan)
    
    def sql(self, query: str) -> "DataFrame":
        """
        Execute a SQL query.
        
        Args:
            query: SQL query string
        """
        from spark_mock.sql.sql_parser import SQLParser
        parser = SQLParser(self)
        return parser.parse(query)
    
    def table(self, tableName: str) -> "DataFrame":
        """Returns the specified table as a DataFrame."""
        from spark_mock.sql.dataframe import DataFrame
        from spark_mock.core.lazy import LazyExecutionPlan, OperationType
        
        lazy_df = self._catalog.getTable(tableName)
        if lazy_df is None:
            raise ValueError(f"Table or view '{tableName}' not found")
        
        plan = LazyExecutionPlan()
        plan.add_operation(OperationType.CREATE_DATAFRAME, table=tableName)
        
        return DataFrame(lazy_df, self, plan)
    
    def range(self, start: int, end: Optional[int] = None, step: int = 1, 
              numPartitions: Optional[int] = None) -> "DataFrame":
        """Create a DataFrame with a single column 'id' containing range of values."""
        from spark_mock.sql.dataframe import DataFrame
        from spark_mock.core.lazy import LazyExecutionPlan, OperationType
        
        if end is None:
            end = start
            start = 0
        
        ids = list(range(start, end, step))
        lazy_df = pl.LazyFrame({"id": ids})
        
        plan = LazyExecutionPlan()
        plan.add_operation(OperationType.CREATE_DATAFRAME, num_rows=len(ids))
        
        return DataFrame(lazy_df, self, plan)
    
    def openUI(self):
        """Open the Spark UI in a web browser."""
        if self._html_ui:
            self._html_ui.open_browser()
        else:
            print("HTML UI is not enabled. Enable with config('spark.mock.ui.html', 'true')")
    
    def stop(self):
        """Stop the SparkSession."""
        if self._html_ui:
            self._html_ui.stop_server()
        self._sc.stop()
        SparkSession._active_session = None
    
    def newSession(self) -> "SparkSession":
        """Returns a new SparkSession with the same configuration."""
        return SparkSession(self._conf)
    
    def __enter__(self) -> "SparkSession":
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
    
    def __repr__(self) -> str:
        return f"SparkSession(appName={self._app_name}, partitions={self._num_partitions})"
