"""
Catalog - manages tables and views.
"""
from typing import Dict, List, Optional, Any
import polars as pl
from dataclasses import dataclass


@dataclass
class Table:
    """Represents a table in the catalog."""
    name: str
    database: Optional[str]
    description: Optional[str]
    tableType: str  # "MANAGED", "EXTERNAL", "VIEW"
    isTemporary: bool


@dataclass
class Database:
    """Represents a database in the catalog."""
    name: str
    description: Optional[str]
    locationUri: str


@dataclass
class Column:
    """Represents a column in a table."""
    name: str
    description: Optional[str]
    dataType: str
    nullable: bool
    isPartition: bool
    isBucket: bool


class Catalog:
    """
    Catalog interface for managing tables and views.
    
    Similar to spark.catalog in PySpark.
    """
    
    def __init__(self, spark_session: "SparkSession"):
        self._spark = spark_session
        self._current_database = "default"
        self._databases: Dict[str, Database] = {
            "default": Database(name="default", description="Default database", locationUri="")
        }
        self._tables: Dict[str, pl.DataFrame] = {}  # name -> DataFrame
        self._temp_views: Dict[str, pl.LazyFrame] = {}  # name -> LazyFrame
        self._global_temp_views: Dict[str, pl.LazyFrame] = {}
    
    def currentDatabase(self) -> str:
        """Returns the current database."""
        return self._current_database
    
    def setCurrentDatabase(self, dbName: str):
        """Sets the current database."""
        if dbName not in self._databases:
            raise ValueError(f"Database '{dbName}' not found")
        self._current_database = dbName
    
    def listDatabases(self) -> List[Database]:
        """Returns a list of databases."""
        return list(self._databases.values())
    
    def createDatabase(self, dbName: str, description: Optional[str] = None):
        """Create a new database."""
        if dbName in self._databases:
            raise ValueError(f"Database '{dbName}' already exists")
        self._databases[dbName] = Database(
            name=dbName,
            description=description,
            locationUri=""
        )
    
    def dropDatabase(self, dbName: str, cascade: bool = False):
        """Drop a database."""
        if dbName == "default":
            raise ValueError("Cannot drop default database")
        if dbName not in self._databases:
            raise ValueError(f"Database '{dbName}' not found")
        del self._databases[dbName]
    
    def listTables(self, dbName: Optional[str] = None) -> List[Table]:
        """Returns a list of tables."""
        tables = []
        
        # Add permanent tables
        for name in self._tables:
            tables.append(Table(
                name=name,
                database=self._current_database,
                description=None,
                tableType="MANAGED",
                isTemporary=False
            ))
        
        # Add temp views
        for name in self._temp_views:
            tables.append(Table(
                name=name,
                database=None,
                description=None,
                tableType="VIEW",
                isTemporary=True
            ))
        
        return tables
    
    def tableExists(self, tableName: str, dbName: Optional[str] = None) -> bool:
        """Check if a table exists."""
        return tableName in self._tables or tableName in self._temp_views
    
    def createTable(self, tableName: str, df: pl.DataFrame):
        """Create a table from DataFrame."""
        self._tables[tableName] = df
    
    def dropTable(self, tableName: str, ifExists: bool = False):
        """Drop a table."""
        if tableName in self._tables:
            del self._tables[tableName]
        elif not ifExists:
            raise ValueError(f"Table '{tableName}' not found")
    
    def createTempView(self, viewName: str, lazy_df: pl.LazyFrame):
        """Create a temporary view."""
        self._temp_views[viewName] = lazy_df
    
    def createOrReplaceTempView(self, viewName: str, lazy_df: pl.LazyFrame):
        """Create or replace a temporary view."""
        self._temp_views[viewName] = lazy_df
    
    def createGlobalTempView(self, viewName: str, lazy_df: pl.LazyFrame):
        """Create a global temporary view."""
        if viewName in self._global_temp_views:
            raise ValueError(f"Global temp view '{viewName}' already exists")
        self._global_temp_views[viewName] = lazy_df
    
    def createOrReplaceGlobalTempView(self, viewName: str, lazy_df: pl.LazyFrame):
        """Create or replace a global temporary view."""
        self._global_temp_views[viewName] = lazy_df
    
    def dropTempView(self, viewName: str) -> bool:
        """Drop a temporary view."""
        if viewName in self._temp_views:
            del self._temp_views[viewName]
            return True
        return False
    
    def dropGlobalTempView(self, viewName: str) -> bool:
        """Drop a global temporary view."""
        if viewName in self._global_temp_views:
            del self._global_temp_views[viewName]
            return True
        return False
    
    def getTable(self, tableName: str) -> Optional[pl.LazyFrame]:
        """Get a table or view as LazyFrame."""
        if tableName in self._temp_views:
            return self._temp_views[tableName]
        if tableName in self._global_temp_views:
            return self._global_temp_views[tableName]
        if tableName in self._tables:
            return self._tables[tableName].lazy()
        return None
    
    def listColumns(self, tableName: str, dbName: Optional[str] = None) -> List[Column]:
        """List columns in a table."""
        lazy_df = self.getTable(tableName)
        if lazy_df is None:
            raise ValueError(f"Table '{tableName}' not found")
        
        schema = lazy_df.collect_schema()
        columns = []
        for name, dtype in schema.items():
            columns.append(Column(
                name=name,
                description=None,
                dataType=str(dtype),
                nullable=True,
                isPartition=False,
                isBucket=False
            ))
        return columns
    
    def cacheTable(self, tableName: str):
        """Cache a table in memory."""
        # In mock, this is a no-op since we're already in-memory
        pass
    
    def uncacheTable(self, tableName: str):
        """Remove a table from cache."""
        pass
    
    def isCached(self, tableName: str) -> bool:
        """Check if a table is cached."""
        return tableName in self._tables or tableName in self._temp_views
    
    def clearCache(self):
        """Clear all cached tables."""
        pass
    
    def refreshTable(self, tableName: str):
        """Refresh a table's cached data."""
        pass
