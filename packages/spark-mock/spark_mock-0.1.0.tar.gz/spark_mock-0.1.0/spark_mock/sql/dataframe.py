"""
DataFrame - the main data structure for Spark Mock.
"""
from typing import Any, Dict, List, Optional, Union, Tuple, Callable
import polars as pl
from rich.table import Table
from rich.console import Console

from spark_mock.sql.column import Column, _to_column
from spark_mock.sql.types import StructType, StructField, _infer_type
from spark_mock.sql.row import Row
from spark_mock.core.lazy import LazyExecutionPlan, OperationType
from spark_mock.core.partition import PartitionInfo


class GroupedData:
    """
    Grouped DataFrame for aggregation operations.
    
    Created by DataFrame.groupBy().
    """
    
    def __init__(self, df: "DataFrame", group_cols: List[str]):
        self._df = df
        self._group_cols = group_cols
    
    def agg(self, *exprs: Union[Column, Dict[str, str]]) -> "DataFrame":
        """Aggregate on the grouped data."""
        from spark_mock.sql.functions import col
        
        # Handle dict input like {"salary": "avg", "age": "max"}
        if len(exprs) == 1 and isinstance(exprs[0], dict):
            agg_dict = exprs[0]
            agg_exprs = []
            for col_name, func_name in agg_dict.items():
                c = pl.col(col_name)
                if func_name == "avg" or func_name == "mean":
                    agg_exprs.append(c.mean().alias(f"avg({col_name})"))
                elif func_name == "sum":
                    agg_exprs.append(c.sum().alias(f"sum({col_name})"))
                elif func_name == "count":
                    agg_exprs.append(c.count().alias(f"count({col_name})"))
                elif func_name == "max":
                    agg_exprs.append(c.max().alias(f"max({col_name})"))
                elif func_name == "min":
                    agg_exprs.append(c.min().alias(f"min({col_name})"))
                elif func_name == "first":
                    agg_exprs.append(c.first().alias(f"first({col_name})"))
                elif func_name == "last":
                    agg_exprs.append(c.last().alias(f"last({col_name})"))
                else:
                    raise ValueError(f"Unknown aggregation function: {func_name}")
        else:
            agg_exprs = [e.expr for e in exprs if isinstance(e, Column)]
        
        # Build new lazy frame
        group_exprs = [pl.col(c) for c in self._group_cols]
        new_lazy = self._df._lazy_df.group_by(group_exprs).agg(agg_exprs)
        
        # Update plan
        plan = self._df._plan.copy()
        plan.add_operation(OperationType.AGG, columns=self._group_cols)
        
        return DataFrame(new_lazy, self._df._spark, plan, self._df._partition_info)
    
    def count(self) -> "DataFrame":
        """Count records in each group."""
        new_lazy = self._df._lazy_df.group_by(self._group_cols).count()
        plan = self._df._plan.copy()
        plan.add_operation(OperationType.AGG, columns=self._group_cols, func="count")
        return DataFrame(new_lazy, self._df._spark, plan, self._df._partition_info)
    
    def sum(self, *cols: str) -> "DataFrame":
        """Sum of values in each group."""
        agg_exprs = [pl.col(c).sum() for c in cols]
        new_lazy = self._df._lazy_df.group_by(self._group_cols).agg(agg_exprs)
        plan = self._df._plan.copy()
        plan.add_operation(OperationType.AGG, columns=self._group_cols, func="sum")
        return DataFrame(new_lazy, self._df._spark, plan, self._df._partition_info)
    
    def avg(self, *cols: str) -> "DataFrame":
        """Average of values in each group."""
        agg_exprs = [pl.col(c).mean().alias(f"avg({c})") for c in cols]
        new_lazy = self._df._lazy_df.group_by(self._group_cols).agg(agg_exprs)
        plan = self._df._plan.copy()
        plan.add_operation(OperationType.AGG, columns=self._group_cols, func="avg")
        return DataFrame(new_lazy, self._df._spark, plan, self._df._partition_info)
    
    def mean(self, *cols: str) -> "DataFrame":
        """Alias for avg."""
        return self.avg(*cols)
    
    def max(self, *cols: str) -> "DataFrame":
        """Max of values in each group."""
        agg_exprs = [pl.col(c).max() for c in cols]
        new_lazy = self._df._lazy_df.group_by(self._group_cols).agg(agg_exprs)
        plan = self._df._plan.copy()
        plan.add_operation(OperationType.AGG, columns=self._group_cols, func="max")
        return DataFrame(new_lazy, self._df._spark, plan, self._df._partition_info)
    
    def min(self, *cols: str) -> "DataFrame":
        """Min of values in each group."""
        agg_exprs = [pl.col(c).min() for c in cols]
        new_lazy = self._df._lazy_df.group_by(self._group_cols).agg(agg_exprs)
        plan = self._df._plan.copy()
        plan.add_operation(OperationType.AGG, columns=self._group_cols, func="min")
        return DataFrame(new_lazy, self._df._spark, plan, self._df._partition_info)
    
    def pivot(self, pivot_col: str) -> "PivotedData":
        """Pivot a column."""
        return PivotedData(self._df, self._group_cols, pivot_col)


class PivotedData:
    """Pivoted data for aggregation."""
    
    def __init__(self, df: "DataFrame", group_cols: List[str], pivot_col: str):
        self._df = df
        self._group_cols = group_cols
        self._pivot_col = pivot_col
    
    def agg(self, *exprs: Column) -> "DataFrame":
        """Aggregate pivoted data."""
        # Polars pivot syntax
        agg_exprs = [e.expr for e in exprs]
        new_lazy = self._df._lazy_df.group_by(self._group_cols).agg(agg_exprs)
        plan = self._df._plan.copy()
        return DataFrame(new_lazy, self._df._spark, plan, self._df._partition_info)


class DataFrame:
    """
    A distributed collection of data organized into named columns.
    
    This is the main data structure for Spark Mock, providing:
    - Lazy evaluation (transformations are not executed until an action is called)
    - Partition simulation
    - Full PySpark-compatible API
    """
    
    def __init__(
        self, 
        lazy_df: pl.LazyFrame,
        spark_session: "SparkSession",
        plan: Optional[LazyExecutionPlan] = None,
        partition_info: Optional[PartitionInfo] = None
    ):
        self._lazy_df = lazy_df
        self._spark = spark_session
        self._plan = plan or LazyExecutionPlan()
        self._partition_info = partition_info
        self._cached = False
        self._cached_df: Optional[pl.DataFrame] = None
        self._broadcast = False
    
    # ================================================================
    # Properties
    # ================================================================
    
    @property
    def columns(self) -> List[str]:
        """Returns column names."""
        return self._lazy_df.collect_schema().names()
    
    @property
    def dtypes(self) -> List[Tuple[str, str]]:
        """Returns column names and types."""
        schema = self._lazy_df.collect_schema()
        return [(name, str(dtype)) for name, dtype in schema.items()]
    
    @property
    def schema(self) -> StructType:
        """Returns the schema."""
        from spark_mock.sql.types import StringType, LongType, DoubleType, BooleanType, DateType
        
        schema = self._lazy_df.collect_schema()
        fields = []
        for name, dtype in schema.items():
            if dtype == pl.Utf8:
                spark_type = StringType()
            elif dtype in (pl.Int64, pl.Int32, pl.Int16, pl.Int8):
                spark_type = LongType()
            elif dtype in (pl.Float64, pl.Float32):
                spark_type = DoubleType()
            elif dtype == pl.Boolean:
                spark_type = BooleanType()
            elif dtype == pl.Date:
                spark_type = DateType()
            else:
                spark_type = StringType()
            fields.append(StructField(name, spark_type))
        return StructType(fields)
    
    @property
    def write(self) -> "DataFrameWriter":
        """Returns a DataFrameWriter."""
        from spark_mock.io.writer import DataFrameWriter
        return DataFrameWriter(self)
    
    @property
    def na(self) -> "DataFrameNaFunctions":
        """Returns a DataFrameNaFunctions for handling null values."""
        return DataFrameNaFunctions(self)
    
    @property
    def stat(self) -> "DataFrameStatFunctions":
        """Returns a DataFrameStatFunctions for statistical functions."""
        return DataFrameStatFunctions(self)
    
    # ================================================================
    # Internal Methods
    # ================================================================
    
    def _collect_internal(self) -> pl.DataFrame:
        """Collect the DataFrame without UI display."""
        if self._cached and self._cached_df is not None:
            return self._cached_df
        return self._lazy_df.collect()
    
    def _execute(self, action: OperationType = OperationType.COLLECT) -> pl.DataFrame:
        """Execute the plan and collect results."""
        if self._cached and self._cached_df is not None:
            return self._cached_df
        
        # Add action to plan
        self._plan.add_operation(action)
        
        # Estimate input rows
        try:
            self._plan.stages[0].input_rows = len(self._collect_internal())
        except:
            pass
        
        # Execute via engine
        result = self._spark._execution_engine.execute(
            self._lazy_df, self._plan, action
        )
        
        if self._cached:
            self._cached_df = result
        
        return result
    
    def _new_df(self, lazy_df: pl.LazyFrame, op_type: OperationType, **params) -> "DataFrame":
        """Create a new DataFrame with updated plan."""
        plan = self._plan.copy()
        plan.add_operation(op_type, **params)
        return DataFrame(lazy_df, self._spark, plan, self._partition_info)
    
    # ================================================================
    # Transformations (Lazy)
    # ================================================================
    
    def select(self, *cols: Union[str, Column, List]) -> "DataFrame":
        """Select columns."""
        # Flatten if list is passed
        if len(cols) == 1 and isinstance(cols[0], list):
            cols = tuple(cols[0])
        
        exprs = []
        col_names = []
        for c in cols:
            if isinstance(c, str):
                if c == "*":
                    exprs.extend([pl.col(name) for name in self.columns])
                    col_names.extend(self.columns)
                else:
                    exprs.append(pl.col(c))
                    col_names.append(c)
            elif isinstance(c, Column):
                exprs.append(c.expr)
                col_names.append(str(c))
            else:
                exprs.append(pl.lit(c))
                col_names.append(str(c))
        
        new_lazy = self._lazy_df.select(exprs)
        return self._new_df(new_lazy, OperationType.SELECT, columns=col_names)
    
    def selectExpr(self, *exprs: str) -> "DataFrame":
        """Select with SQL expressions."""
        from spark_mock.sql.functions import expr
        columns = [expr(e) for e in exprs]
        return self.select(*columns)
    
    def filter(self, condition: Union[Column, str]) -> "DataFrame":
        """Filter rows."""
        if isinstance(condition, str):
            # Simple string condition - would need a parser for complex cases
            from spark_mock.sql.functions import expr
            condition = expr(condition)
        
        new_lazy = self._lazy_df.filter(condition.expr)
        return self._new_df(new_lazy, OperationType.FILTER, condition=str(condition))
    
    def where(self, condition: Union[Column, str]) -> "DataFrame":
        """Alias for filter."""
        return self.filter(condition)
    
    def groupBy(self, *cols: Union[str, Column]) -> GroupedData:
        """Group by columns."""
        col_names = []
        for c in cols:
            if isinstance(c, str):
                col_names.append(c)
            elif isinstance(c, Column):
                col_names.append(str(c))
        
        # Add to plan
        self._plan.add_operation(OperationType.GROUP_BY, columns=col_names)
        
        return GroupedData(self, col_names)
    
    def groupby(self, *cols: Union[str, Column]) -> GroupedData:
        """Alias for groupBy."""
        return self.groupBy(*cols)
    
    def agg(self, *exprs: Union[Column, Dict[str, str]]) -> "DataFrame":
        """Aggregate without grouping."""
        if len(exprs) == 1 and isinstance(exprs[0], dict):
            agg_dict = exprs[0]
            agg_exprs = []
            for col_name, func_name in agg_dict.items():
                c = pl.col(col_name)
                if func_name in ("avg", "mean"):
                    agg_exprs.append(c.mean().alias(f"avg({col_name})"))
                elif func_name == "sum":
                    agg_exprs.append(c.sum().alias(f"sum({col_name})"))
                elif func_name == "count":
                    agg_exprs.append(c.count().alias(f"count({col_name})"))
                elif func_name == "max":
                    agg_exprs.append(c.max().alias(f"max({col_name})"))
                elif func_name == "min":
                    agg_exprs.append(c.min().alias(f"min({col_name})"))
        else:
            agg_exprs = [e.expr for e in exprs if isinstance(e, Column)]
        
        new_lazy = self._lazy_df.select(agg_exprs)
        return self._new_df(new_lazy, OperationType.AGG)
    
    def join(
        self, 
        other: "DataFrame", 
        on: Union[str, List[str], Column] = None,
        how: str = "inner"
    ) -> "DataFrame":
        """Join with another DataFrame."""
        # Determine join columns
        if on is None:
            # Find common columns
            on = list(set(self.columns) & set(other.columns))
        elif isinstance(on, str):
            on = [on]
        elif isinstance(on, Column):
            on = [str(on)]
        
        # Map join type
        how_map = {
            "inner": "inner",
            "outer": "full",
            "full": "full",
            "full_outer": "full",
            "left": "left",
            "left_outer": "left",
            "right": "right",
            "right_outer": "right",
            "cross": "cross",
            "semi": "semi",
            "left_semi": "semi",
            "anti": "anti",
            "left_anti": "anti",
        }
        polars_how = how_map.get(how.lower(), "inner")
        
        if polars_how == "cross":
            new_lazy = self._lazy_df.join(other._lazy_df, how="cross")
        else:
            new_lazy = self._lazy_df.join(other._lazy_df, on=on, how=polars_how)
        
        plan = self._plan.copy()
        plan.add_operation(OperationType.JOIN, how=how, on=on)
        
        return DataFrame(new_lazy, self._spark, plan, self._partition_info)
    
    def crossJoin(self, other: "DataFrame") -> "DataFrame":
        """Cross join with another DataFrame."""
        return self.join(other, how="cross")
    
    def orderBy(self, *cols: Union[str, Column], ascending: Union[bool, List[bool]] = True) -> "DataFrame":
        """Order by columns."""
        if isinstance(ascending, bool):
            ascending = [ascending] * len(cols)
        
        sort_exprs = []
        col_names = []
        for i, c in enumerate(cols):
            desc = not ascending[i] if i < len(ascending) else False
            if isinstance(c, str):
                sort_exprs.append(pl.col(c).sort(descending=desc))
                col_names.append(c)
            elif isinstance(c, Column):
                sort_exprs.append(c.expr.sort(descending=desc))
                col_names.append(str(c))
        
        new_lazy = self._lazy_df.sort(
            [c if isinstance(c, str) else str(c) for c in cols],
            descending=[not a for a in ascending]
        )
        return self._new_df(new_lazy, OperationType.ORDER_BY, columns=col_names)
    
    def sort(self, *cols: Union[str, Column], ascending: Union[bool, List[bool]] = True) -> "DataFrame":
        """Alias for orderBy."""
        return self.orderBy(*cols, ascending=ascending)
    
    def limit(self, n: int) -> "DataFrame":
        """Limit to n rows."""
        new_lazy = self._lazy_df.limit(n)
        return self._new_df(new_lazy, OperationType.LIMIT, n=n)
    
    def withColumn(self, colName: str, col: Column) -> "DataFrame":
        """Add or replace a column."""
        new_lazy = self._lazy_df.with_columns(col.expr.alias(colName))
        return self._new_df(new_lazy, OperationType.WITH_COLUMN, column=colName)
    
    def withColumns(self, *colsMap: Dict[str, Column]) -> "DataFrame":
        """Add or replace multiple columns."""
        if len(colsMap) == 1 and isinstance(colsMap[0], dict):
            colsMap = colsMap[0]
        else:
            colsMap = dict(colsMap)
        
        exprs = [v.expr.alias(k) for k, v in colsMap.items()]
        new_lazy = self._lazy_df.with_columns(exprs)
        return self._new_df(new_lazy, OperationType.WITH_COLUMN)
    
    def withColumnRenamed(self, existing: str, new: str) -> "DataFrame":
        """Rename a column."""
        new_lazy = self._lazy_df.rename({existing: new})
        return self._new_df(new_lazy, OperationType.WITH_COLUMN_RENAMED, 
                           existing=existing, new=new)
    
    def drop(self, *cols: Union[str, Column]) -> "DataFrame":
        """Drop columns."""
        col_names = [c if isinstance(c, str) else str(c) for c in cols]
        new_lazy = self._lazy_df.drop(col_names)
        return self._new_df(new_lazy, OperationType.DROP, columns=col_names)
    
    def distinct(self) -> "DataFrame":
        """Return distinct rows."""
        new_lazy = self._lazy_df.unique()
        return self._new_df(new_lazy, OperationType.DISTINCT)
    
    def dropDuplicates(self, subset: Optional[List[str]] = None) -> "DataFrame":
        """Drop duplicate rows."""
        if subset:
            new_lazy = self._lazy_df.unique(subset=subset)
        else:
            new_lazy = self._lazy_df.unique()
        return self._new_df(new_lazy, OperationType.DISTINCT)
    
    def drop_duplicates(self, subset: Optional[List[str]] = None) -> "DataFrame":
        """Alias for dropDuplicates."""
        return self.dropDuplicates(subset)
    
    def union(self, other: "DataFrame") -> "DataFrame":
        """Union with another DataFrame."""
        new_lazy = pl.concat([self._lazy_df, other._lazy_df])
        return self._new_df(new_lazy, OperationType.UNION)
    
    def unionAll(self, other: "DataFrame") -> "DataFrame":
        """Alias for union."""
        return self.union(other)
    
    def unionByName(self, other: "DataFrame", allowMissingColumns: bool = False) -> "DataFrame":
        """Union by column names."""
        if allowMissingColumns:
            # Add missing columns with nulls
            all_cols = set(self.columns) | set(other.columns)
            self_lazy = self._lazy_df
            other_lazy = other._lazy_df
            
            for col in all_cols:
                if col not in self.columns:
                    self_lazy = self_lazy.with_columns(pl.lit(None).alias(col))
                if col not in other.columns:
                    other_lazy = other_lazy.with_columns(pl.lit(None).alias(col))
            
            new_lazy = pl.concat([self_lazy, other_lazy])
        else:
            new_lazy = pl.concat([self._lazy_df, other._lazy_df])
        
        return self._new_df(new_lazy, OperationType.UNION)
    
    def intersect(self, other: "DataFrame") -> "DataFrame":
        """Return intersection with another DataFrame."""
        new_lazy = self._lazy_df.join(other._lazy_df, on=self.columns, how="semi").unique()
        return self._new_df(new_lazy, OperationType.DISTINCT)
    
    def exceptAll(self, other: "DataFrame") -> "DataFrame":
        """Return rows in this DataFrame but not in other."""
        new_lazy = self._lazy_df.join(other._lazy_df, on=self.columns, how="anti")
        return self._new_df(new_lazy, OperationType.DISTINCT)
    
    def subtract(self, other: "DataFrame") -> "DataFrame":
        """Alias for exceptAll."""
        return self.exceptAll(other)
    
    def sample(
        self, 
        withReplacement: bool = False, 
        fraction: float = None,
        seed: int = None
    ) -> "DataFrame":
        """Sample from the DataFrame."""
        if fraction is None:
            fraction = 0.5
        
        new_lazy = self._lazy_df.collect().sample(
            fraction=fraction, 
            with_replacement=withReplacement,
            seed=seed
        ).lazy()
        
        return self._new_df(new_lazy, OperationType.LIMIT)
    
    def randomSplit(self, weights: List[float], seed: int = None) -> List["DataFrame"]:
        """Split DataFrame randomly."""
        import random
        if seed:
            random.seed(seed)
        
        # Normalize weights
        total = sum(weights)
        weights = [w / total for w in weights]
        
        df = self._collect_internal()
        n = len(df)
        
        # Assign each row to a split
        splits = [[] for _ in weights]
        for i in range(n):
            r = random.random()
            cumsum = 0
            for j, w in enumerate(weights):
                cumsum += w
                if r <= cumsum:
                    splits[j].append(i)
                    break
        
        result = []
        for indices in splits:
            if indices:
                split_df = df[indices]
                result.append(DataFrame(split_df.lazy(), self._spark, 
                                        self._plan.copy(), self._partition_info))
            else:
                result.append(DataFrame(pl.LazyFrame({}), self._spark,
                                        self._plan.copy(), self._partition_info))
        
        return result
    
    def repartition(self, numPartitions: int, *cols: Union[str, Column]) -> "DataFrame":
        """Repartition the DataFrame."""
        partition_manager = self._spark._execution_engine.partition_manager
        if self._partition_info:
            col_names = [c if isinstance(c, str) else str(c) for c in cols] if cols else None
            new_partition_info = partition_manager.repartition(
                self._partition_info, numPartitions, col_names
            )
        else:
            new_partition_info = partition_manager.create_partitions(
                self._collect_internal(), numPartitions
            )
        
        plan = self._plan.copy()
        plan.add_operation(OperationType.REPARTITION, num_partitions=numPartitions)
        
        return DataFrame(self._lazy_df, self._spark, plan, new_partition_info)
    
    def coalesce(self, numPartitions: int) -> "DataFrame":
        """Reduce the number of partitions."""
        partition_manager = self._spark._execution_engine.partition_manager
        if self._partition_info:
            new_partition_info = partition_manager.coalesce(
                self._partition_info, numPartitions
            )
        else:
            new_partition_info = partition_manager.create_partitions(
                self._collect_internal(), numPartitions
            )
        
        plan = self._plan.copy()
        plan.add_operation(OperationType.COALESCE, num_partitions=numPartitions)
        
        return DataFrame(self._lazy_df, self._spark, plan, new_partition_info)
    
    def cache(self) -> "DataFrame":
        """Cache the DataFrame."""
        self._cached = True
        return self
    
    def persist(self, storageLevel=None) -> "DataFrame":
        """Persist the DataFrame."""
        self._cached = True
        return self
    
    def unpersist(self, blocking: bool = False) -> "DataFrame":
        """Unpersist the DataFrame."""
        self._cached = False
        self._cached_df = None
        return self
    
    def alias(self, alias: str) -> "DataFrame":
        """Set an alias for the DataFrame."""
        # In mock, just return self (alias is mainly for SQL)
        return self
    
    def toDF(self, *cols: str) -> "DataFrame":
        """Rename columns."""
        current_cols = self.columns
        if len(cols) != len(current_cols):
            raise ValueError(f"Number of columns doesn't match: {len(cols)} vs {len(current_cols)}")
        
        rename_map = {old: new for old, new in zip(current_cols, cols)}
        new_lazy = self._lazy_df.rename(rename_map)
        return self._new_df(new_lazy, OperationType.WITH_COLUMN_RENAMED)
    
    def transform(self, func: Callable[["DataFrame"], "DataFrame"]) -> "DataFrame":
        """Apply a function to the DataFrame."""
        return func(self)
    
    # ================================================================
    # Actions (Trigger Execution)
    # ================================================================
    
    def show(self, n: int = 20, truncate: Union[bool, int] = True, vertical: bool = False):
        """Display the first n rows."""
        result = self._execute(OperationType.SHOW)
        
        if vertical:
            for i, row in enumerate(result.head(n).iter_rows(named=True)):
                print(f"-RECORD {i}" + "-" * 20)
                for k, v in row.items():
                    print(f" {k}: {v}")
        else:
            # Use rich table for nice display
            console = Console()
            table = Table(show_header=True, header_style="bold")
            
            for col in result.columns:
                table.add_column(col)
            
            for row in result.head(n).iter_rows():
                str_row = []
                for val in row:
                    s = str(val) if val is not None else "null"
                    if isinstance(truncate, int) and len(s) > truncate:
                        s = s[:truncate] + "..."
                    elif truncate is True and len(s) > 20:
                        s = s[:20] + "..."
                    str_row.append(s)
                table.add_row(*str_row)
            
            console.print(table)
    
    def collect(self) -> List[Row]:
        """Collect all data as a list of Rows."""
        result = self._execute(OperationType.COLLECT)
        
        rows = []
        columns = result.columns
        for row_tuple in result.iter_rows():
            row_dict = dict(zip(columns, row_tuple))
            rows.append(Row(**row_dict))
        
        return rows
    
    def count(self) -> int:
        """Count the number of rows."""
        result = self._execute(OperationType.COUNT)
        return len(result)
    
    def first(self) -> Optional[Row]:
        """Return the first row."""
        rows = self.take(1)
        return rows[0] if rows else None
    
    def head(self, n: int = 1) -> List[Row]:
        """Return the first n rows."""
        return self.take(n)
    
    def take(self, n: int) -> List[Row]:
        """Take the first n rows."""
        limited = self.limit(n)
        result = limited._execute(OperationType.TAKE)
        
        rows = []
        columns = result.columns
        for row_tuple in result.iter_rows():
            row_dict = dict(zip(columns, row_tuple))
            rows.append(Row(**row_dict))
        
        return rows
    
    def toPandas(self):
        """Convert to Pandas DataFrame."""
        result = self._execute(OperationType.COLLECT)
        return result.to_pandas()
    
    def toLocalIterator(self):
        """Return an iterator of Rows."""
        result = self._execute(OperationType.COLLECT)
        columns = result.columns
        for row_tuple in result.iter_rows():
            yield Row(**dict(zip(columns, row_tuple)))
    
    def foreach(self, f: Callable[[Row], None]):
        """Apply a function to each row."""
        for row in self.collect():
            f(row)
    
    def foreachPartition(self, f: Callable[[List[Row]], None]):
        """Apply a function to each partition."""
        rows = self.collect()
        f(rows)
    
    def printSchema(self):
        """Print the schema."""
        lines = ["root"]
        for field in self.schema:
            nullable_str = "nullable = true" if field.nullable else "nullable = false"
            lines.append(f" |-- {field.name}: {field.dataType.simpleString()} ({nullable_str})")
        
        schema_str = "\n".join(lines)
        self._spark._console_ui.display_schema(schema_str)
    
    def explain(self, extended: bool = False, mode: str = None):
        """Print the execution plan."""
        plan_str = self._plan.explain(extended)
        self._spark._console_ui.display_explain(plan_str)
    
    def describe(self, *cols: str) -> "DataFrame":
        """Compute basic statistics."""
        if not cols:
            cols = self.columns
        
        result_data = []
        stats = ["count", "mean", "stddev", "min", "max"]
        
        df = self._collect_internal()
        
        for stat in stats:
            row = {"summary": stat}
            for col in cols:
                if stat == "count":
                    row[col] = str(df[col].count())
                elif stat == "mean":
                    try:
                        row[col] = str(df[col].mean())
                    except:
                        row[col] = None
                elif stat == "stddev":
                    try:
                        row[col] = str(df[col].std())
                    except:
                        row[col] = None
                elif stat == "min":
                    row[col] = str(df[col].min())
                elif stat == "max":
                    row[col] = str(df[col].max())
            result_data.append(row)
        
        result_df = pl.DataFrame(result_data)
        return DataFrame(result_df.lazy(), self._spark, LazyExecutionPlan())
    
    def summary(self, *statistics: str) -> "DataFrame":
        """Compute specified statistics."""
        return self.describe(*self.columns)
    
    def isEmpty(self) -> bool:
        """Check if DataFrame is empty."""
        return self.count() == 0
    
    # ================================================================
    # Views
    # ================================================================
    
    def createTempView(self, name: str):
        """Create a temporary view."""
        if self._spark._catalog.tableExists(name):
            raise ValueError(f"Temp view '{name}' already exists")
        self._spark._catalog.createTempView(name, self._lazy_df)
    
    def createOrReplaceTempView(self, name: str):
        """Create or replace a temporary view."""
        self._spark._catalog.createOrReplaceTempView(name, self._lazy_df)
    
    def createGlobalTempView(self, name: str):
        """Create a global temporary view."""
        self._spark._catalog.createGlobalTempView(name, self._lazy_df)
    
    def createOrReplaceGlobalTempView(self, name: str):
        """Create or replace a global temporary view."""
        self._spark._catalog.createOrReplaceGlobalTempView(name, self._lazy_df)
    
    # ================================================================
    # Special Methods
    # ================================================================
    
    def __repr__(self) -> str:
        cols = ", ".join(self.columns[:5])
        if len(self.columns) > 5:
            cols += "..."
        return f"DataFrame[{cols}]"
    
    def __getitem__(self, item) -> Union[Column, "DataFrame"]:
        if isinstance(item, str):
            return Column(item)
        elif isinstance(item, int):
            return Column(self.columns[item])
        elif isinstance(item, (list, tuple)):
            return self.select(*item)
        elif isinstance(item, Column):
            return self.filter(item)
        else:
            raise TypeError(f"Unsupported index type: {type(item)}")
    
    def __getattr__(self, name: str) -> Column:
        if name.startswith("_"):
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
        if name in self.columns:
            return Column(name)
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")


class DataFrameNaFunctions:
    """Functions for handling null values."""
    
    def __init__(self, df: DataFrame):
        self._df = df
    
    def drop(
        self, 
        how: str = "any", 
        thresh: int = None, 
        subset: List[str] = None
    ) -> DataFrame:
        """Drop rows with null values."""
        if subset:
            cols = subset
        else:
            cols = self._df.columns
        
        if thresh is not None:
            # Keep rows with at least thresh non-null values
            condition = None
            for col in cols:
                is_not_null = pl.col(col).is_not_null()
                if condition is None:
                    condition = is_not_null.cast(pl.Int32)
                else:
                    condition = condition + is_not_null.cast(pl.Int32)
            new_lazy = self._df._lazy_df.filter(condition >= thresh)
        elif how == "any":
            new_lazy = self._df._lazy_df.drop_nulls(subset=cols)
        else:  # how == "all"
            condition = pl.lit(False)
            for col in cols:
                condition = condition | pl.col(col).is_not_null()
            new_lazy = self._df._lazy_df.filter(condition)
        
        return self._df._new_df(new_lazy, OperationType.FILTER)
    
    def fill(
        self, 
        value: Any, 
        subset: List[str] = None
    ) -> DataFrame:
        """Fill null values."""
        if subset:
            cols = subset
        else:
            cols = self._df.columns
        
        fill_exprs = [pl.col(c).fill_null(value) for c in cols]
        new_lazy = self._df._lazy_df.with_columns(fill_exprs)
        
        return self._df._new_df(new_lazy, OperationType.WITH_COLUMN)
    
    def replace(
        self, 
        to_replace: Any, 
        value: Any, 
        subset: List[str] = None
    ) -> DataFrame:
        """Replace values."""
        if subset:
            cols = subset
        else:
            cols = self._df.columns
        
        replace_exprs = [
            pl.when(pl.col(c) == to_replace).then(value).otherwise(pl.col(c)).alias(c)
            for c in cols
        ]
        new_lazy = self._df._lazy_df.with_columns(replace_exprs)
        
        return self._df._new_df(new_lazy, OperationType.WITH_COLUMN)


class DataFrameStatFunctions:
    """Statistical functions for DataFrame."""
    
    def __init__(self, df: DataFrame):
        self._df = df
    
    def corr(self, col1: str, col2: str, method: str = "pearson") -> float:
        """Calculate correlation between two columns."""
        result = self._df._collect_internal()
        return result[col1].to_numpy().astype(float).dot(
            result[col2].to_numpy().astype(float)
        ) / len(result)
    
    def cov(self, col1: str, col2: str) -> float:
        """Calculate covariance between two columns."""
        result = self._df._collect_internal()
        import numpy as np
        return np.cov(result[col1].to_numpy(), result[col2].to_numpy())[0, 1]
    
    def crosstab(self, col1: str, col2: str) -> DataFrame:
        """Compute a crosstab of two columns."""
        result = self._df._collect_internal()
        pivot = result.pivot(
            values=col2, 
            index=col1, 
            columns=col2,
            aggregate_function="len"
        )
        return DataFrame(pivot.lazy(), self._df._spark, LazyExecutionPlan())
    
    def freqItems(self, cols: List[str], support: float = 0.01) -> DataFrame:
        """Find frequent items."""
        return self._df.select(*cols).distinct()
    
    def sampleBy(
        self, 
        col: str, 
        fractions: Dict[Any, float], 
        seed: int = None
    ) -> DataFrame:
        """Stratified sampling."""
        import random
        if seed:
            random.seed(seed)
        
        result = self._df._collect_internal()
        sampled_rows = []
        
        for value, fraction in fractions.items():
            subset = result.filter(pl.col(col) == value)
            n_samples = int(len(subset) * fraction)
            if n_samples > 0:
                sampled = subset.sample(n=n_samples, seed=seed)
                sampled_rows.append(sampled)
        
        if sampled_rows:
            combined = pl.concat(sampled_rows)
            return DataFrame(combined.lazy(), self._df._spark, LazyExecutionPlan())
        
        return DataFrame(pl.LazyFrame({}), self._df._spark, LazyExecutionPlan())
