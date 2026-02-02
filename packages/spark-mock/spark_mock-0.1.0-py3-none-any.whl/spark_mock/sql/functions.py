"""
Spark SQL Functions - mirrors pyspark.sql.functions
"""
from typing import Any, Union, List, Optional
import polars as pl
from spark_mock.sql.column import Column


# ============================================================
# Column Reference Functions
# ============================================================

def col(name: str) -> Column:
    """Returns a Column based on the given column name."""
    return Column(name)


def column(name: str) -> Column:
    """Alias for col()."""
    return col(name)


def lit(value: Any) -> Column:
    """Creates a Column of literal value."""
    return Column(pl.lit(value))


# ============================================================
# Aggregation Functions
# ============================================================

def sum(col_or_name: Union[str, Column]) -> Column:
    """Aggregate function: sum of values."""
    c = Column(col_or_name) if isinstance(col_or_name, str) else col_or_name
    return Column(c.expr.sum())


def avg(col_or_name: Union[str, Column]) -> Column:
    """Aggregate function: average of values."""
    c = Column(col_or_name) if isinstance(col_or_name, str) else col_or_name
    return Column(c.expr.mean())


def mean(col_or_name: Union[str, Column]) -> Column:
    """Alias for avg()."""
    return avg(col_or_name)


def count(col_or_name: Union[str, Column]) -> Column:
    """Aggregate function: count of values."""
    if col_or_name == "*":
        return Column(pl.len())
    c = Column(col_or_name) if isinstance(col_or_name, str) else col_or_name
    return Column(c.expr.count())


def countDistinct(*cols: Union[str, Column]) -> Column:
    """Aggregate function: count of distinct values."""
    if len(cols) == 1:
        c = Column(cols[0]) if isinstance(cols[0], str) else cols[0]
        return Column(c.expr.n_unique())
    # For multiple columns, we need to combine them
    exprs = [Column(c).expr if isinstance(c, str) else c.expr for c in cols]
    return Column(pl.struct(exprs).n_unique())


def max(col_or_name: Union[str, Column]) -> Column:
    """Aggregate function: maximum value."""
    c = Column(col_or_name) if isinstance(col_or_name, str) else col_or_name
    return Column(c.expr.max())


def min(col_or_name: Union[str, Column]) -> Column:
    """Aggregate function: minimum value."""
    c = Column(col_or_name) if isinstance(col_or_name, str) else col_or_name
    return Column(c.expr.min())


def first(col_or_name: Union[str, Column], ignorenulls: bool = False) -> Column:
    """Aggregate function: first value."""
    c = Column(col_or_name) if isinstance(col_or_name, str) else col_or_name
    return Column(c.expr.first())


def last(col_or_name: Union[str, Column], ignorenulls: bool = False) -> Column:
    """Aggregate function: last value."""
    c = Column(col_or_name) if isinstance(col_or_name, str) else col_or_name
    return Column(c.expr.last())


def collect_list(col_or_name: Union[str, Column]) -> Column:
    """Aggregate function: collect values into a list."""
    c = Column(col_or_name) if isinstance(col_or_name, str) else col_or_name
    return Column(c.expr.implode())


def collect_set(col_or_name: Union[str, Column]) -> Column:
    """Aggregate function: collect unique values into a list."""
    c = Column(col_or_name) if isinstance(col_or_name, str) else col_or_name
    return Column(c.expr.unique())


def stddev(col_or_name: Union[str, Column]) -> Column:
    """Aggregate function: sample standard deviation."""
    c = Column(col_or_name) if isinstance(col_or_name, str) else col_or_name
    return Column(c.expr.std())


def stddev_pop(col_or_name: Union[str, Column]) -> Column:
    """Aggregate function: population standard deviation."""
    c = Column(col_or_name) if isinstance(col_or_name, str) else col_or_name
    return Column(c.expr.std(ddof=0))


def variance(col_or_name: Union[str, Column]) -> Column:
    """Aggregate function: sample variance."""
    c = Column(col_or_name) if isinstance(col_or_name, str) else col_or_name
    return Column(c.expr.var())


def var_pop(col_or_name: Union[str, Column]) -> Column:
    """Aggregate function: population variance."""
    c = Column(col_or_name) if isinstance(col_or_name, str) else col_or_name
    return Column(c.expr.var(ddof=0))


# ============================================================
# Conditional Functions
# ============================================================

def when(condition: Column, value: Any) -> Column:
    """Evaluates conditions and returns value when condition is true."""
    val_expr = value.expr if isinstance(value, Column) else pl.lit(value)
    return Column(pl.when(condition.expr).then(val_expr))


def coalesce(*cols: Union[str, Column]) -> Column:
    """Returns the first non-null value."""
    exprs = [Column(c).expr if isinstance(c, str) else c.expr for c in cols]
    return Column(pl.coalesce(exprs))


def isnull(col_or_name: Union[str, Column]) -> Column:
    """Check if value is null."""
    c = Column(col_or_name) if isinstance(col_or_name, str) else col_or_name
    return Column(c.expr.is_null())


def isnan(col_or_name: Union[str, Column]) -> Column:
    """Check if value is NaN."""
    c = Column(col_or_name) if isinstance(col_or_name, str) else col_or_name
    return Column(c.expr.is_nan())


def ifnull(col1: Union[str, Column], col2: Union[str, Column]) -> Column:
    """Returns col2 if col1 is null."""
    return coalesce(col1, col2)


def nullif(col1: Union[str, Column], col2: Union[str, Column]) -> Column:
    """Returns null if col1 equals col2, otherwise returns col1."""
    c1 = Column(col1) if isinstance(col1, str) else col1
    c2 = Column(col2) if isinstance(col2, str) else col2
    return when(c1 == c2, lit(None)).otherwise(c1)


# ============================================================
# String Functions
# ============================================================

def concat(*cols: Union[str, Column]) -> Column:
    """Concatenates multiple columns together."""
    exprs = [Column(c).expr if isinstance(c, str) else c.expr for c in cols]
    return Column(pl.concat_str(exprs))


def concat_ws(sep: str, *cols: Union[str, Column]) -> Column:
    """Concatenates multiple columns with separator."""
    exprs = [Column(c).expr if isinstance(c, str) else c.expr for c in cols]
    return Column(pl.concat_str(exprs, separator=sep))


def substring(col_or_name: Union[str, Column], pos: int, length: int) -> Column:
    """Substring extraction."""
    c = Column(col_or_name) if isinstance(col_or_name, str) else col_or_name
    return Column(c.expr.str.slice(pos - 1, length))


def length(col_or_name: Union[str, Column]) -> Column:
    """String length."""
    c = Column(col_or_name) if isinstance(col_or_name, str) else col_or_name
    return Column(c.expr.str.len_chars())


def lower(col_or_name: Union[str, Column]) -> Column:
    """Convert to lowercase."""
    c = Column(col_or_name) if isinstance(col_or_name, str) else col_or_name
    return Column(c.expr.str.to_lowercase())


def upper(col_or_name: Union[str, Column]) -> Column:
    """Convert to uppercase."""
    c = Column(col_or_name) if isinstance(col_or_name, str) else col_or_name
    return Column(c.expr.str.to_uppercase())


def trim(col_or_name: Union[str, Column]) -> Column:
    """Trim whitespace."""
    c = Column(col_or_name) if isinstance(col_or_name, str) else col_or_name
    return Column(c.expr.str.strip_chars())


def ltrim(col_or_name: Union[str, Column]) -> Column:
    """Left trim."""
    c = Column(col_or_name) if isinstance(col_or_name, str) else col_or_name
    return Column(c.expr.str.strip_chars_start())


def rtrim(col_or_name: Union[str, Column]) -> Column:
    """Right trim."""
    c = Column(col_or_name) if isinstance(col_or_name, str) else col_or_name
    return Column(c.expr.str.strip_chars_end())


def lpad(col_or_name: Union[str, Column], length: int, pad: str = " ") -> Column:
    """Left pad string."""
    c = Column(col_or_name) if isinstance(col_or_name, str) else col_or_name
    return Column(c.expr.str.pad_start(length, pad))


def rpad(col_or_name: Union[str, Column], length: int, pad: str = " ") -> Column:
    """Right pad string."""
    c = Column(col_or_name) if isinstance(col_or_name, str) else col_or_name
    return Column(c.expr.str.pad_end(length, pad))


def split(col_or_name: Union[str, Column], pattern: str) -> Column:
    """Split string by pattern."""
    c = Column(col_or_name) if isinstance(col_or_name, str) else col_or_name
    return Column(c.expr.str.split(pattern))


def regexp_replace(col_or_name: Union[str, Column], pattern: str, replacement: str) -> Column:
    """Replace regex pattern."""
    c = Column(col_or_name) if isinstance(col_or_name, str) else col_or_name
    return Column(c.expr.str.replace_all(pattern, replacement))


def regexp_extract(col_or_name: Union[str, Column], pattern: str, idx: int = 0) -> Column:
    """Extract regex pattern."""
    c = Column(col_or_name) if isinstance(col_or_name, str) else col_or_name
    return Column(c.expr.str.extract(pattern, idx))


def initcap(col_or_name: Union[str, Column]) -> Column:
    """Initial capitalize."""
    c = Column(col_or_name) if isinstance(col_or_name, str) else col_or_name
    return Column(c.expr.str.to_titlecase())


def reverse(col_or_name: Union[str, Column]) -> Column:
    """Reverse string."""
    c = Column(col_or_name) if isinstance(col_or_name, str) else col_or_name
    return Column(c.expr.str.reverse())


# ============================================================
# Date/Time Functions
# ============================================================

def current_date() -> Column:
    """Returns current date."""
    import datetime
    return Column(pl.lit(datetime.date.today()))


def current_timestamp() -> Column:
    """Returns current timestamp."""
    import datetime
    return Column(pl.lit(datetime.datetime.now()))


def year(col_or_name: Union[str, Column]) -> Column:
    """Extract year."""
    c = Column(col_or_name) if isinstance(col_or_name, str) else col_or_name
    return Column(c.expr.dt.year())


def month(col_or_name: Union[str, Column]) -> Column:
    """Extract month."""
    c = Column(col_or_name) if isinstance(col_or_name, str) else col_or_name
    return Column(c.expr.dt.month())


def dayofmonth(col_or_name: Union[str, Column]) -> Column:
    """Extract day of month."""
    c = Column(col_or_name) if isinstance(col_or_name, str) else col_or_name
    return Column(c.expr.dt.day())


def day(col_or_name: Union[str, Column]) -> Column:
    """Alias for dayofmonth."""
    return dayofmonth(col_or_name)


def dayofweek(col_or_name: Union[str, Column]) -> Column:
    """Extract day of week (1=Sunday, 7=Saturday)."""
    c = Column(col_or_name) if isinstance(col_or_name, str) else col_or_name
    return Column(c.expr.dt.weekday() + 1)


def dayofyear(col_or_name: Union[str, Column]) -> Column:
    """Extract day of year."""
    c = Column(col_or_name) if isinstance(col_or_name, str) else col_or_name
    return Column(c.expr.dt.ordinal_day())


def hour(col_or_name: Union[str, Column]) -> Column:
    """Extract hour."""
    c = Column(col_or_name) if isinstance(col_or_name, str) else col_or_name
    return Column(c.expr.dt.hour())


def minute(col_or_name: Union[str, Column]) -> Column:
    """Extract minute."""
    c = Column(col_or_name) if isinstance(col_or_name, str) else col_or_name
    return Column(c.expr.dt.minute())


def second(col_or_name: Union[str, Column]) -> Column:
    """Extract second."""
    c = Column(col_or_name) if isinstance(col_or_name, str) else col_or_name
    return Column(c.expr.dt.second())


def weekofyear(col_or_name: Union[str, Column]) -> Column:
    """Extract week of year."""
    c = Column(col_or_name) if isinstance(col_or_name, str) else col_or_name
    return Column(c.expr.dt.week())


def quarter(col_or_name: Union[str, Column]) -> Column:
    """Extract quarter."""
    c = Column(col_or_name) if isinstance(col_or_name, str) else col_or_name
    return Column(c.expr.dt.quarter())


def date_format(col_or_name: Union[str, Column], format: str) -> Column:
    """Format date."""
    c = Column(col_or_name) if isinstance(col_or_name, str) else col_or_name
    return Column(c.expr.dt.strftime(format))


def to_date(col_or_name: Union[str, Column], format: Optional[str] = None) -> Column:
    """Convert to date."""
    c = Column(col_or_name) if isinstance(col_or_name, str) else col_or_name
    if format:
        return Column(c.expr.str.to_date(format))
    return Column(c.expr.cast(pl.Date))


def to_timestamp(col_or_name: Union[str, Column], format: Optional[str] = None) -> Column:
    """Convert to timestamp."""
    c = Column(col_or_name) if isinstance(col_or_name, str) else col_or_name
    if format:
        return Column(c.expr.str.to_datetime(format))
    return Column(c.expr.cast(pl.Datetime))


def datediff(end: Union[str, Column], start: Union[str, Column]) -> Column:
    """Difference in days between two dates."""
    e = Column(end) if isinstance(end, str) else end
    s = Column(start) if isinstance(start, str) else start
    return Column((e.expr.cast(pl.Date) - s.expr.cast(pl.Date)).dt.total_days())


def date_add(col_or_name: Union[str, Column], days: int) -> Column:
    """Add days to date."""
    c = Column(col_or_name) if isinstance(col_or_name, str) else col_or_name
    return Column(c.expr + pl.duration(days=days))


def date_sub(col_or_name: Union[str, Column], days: int) -> Column:
    """Subtract days from date."""
    c = Column(col_or_name) if isinstance(col_or_name, str) else col_or_name
    return Column(c.expr - pl.duration(days=days))


# ============================================================
# Math Functions
# ============================================================

def abs(col_or_name: Union[str, Column]) -> Column:
    """Absolute value."""
    c = Column(col_or_name) if isinstance(col_or_name, str) else col_or_name
    return Column(c.expr.abs())


def sqrt(col_or_name: Union[str, Column]) -> Column:
    """Square root."""
    c = Column(col_or_name) if isinstance(col_or_name, str) else col_or_name
    return Column(c.expr.sqrt())


def exp(col_or_name: Union[str, Column]) -> Column:
    """Exponential."""
    c = Column(col_or_name) if isinstance(col_or_name, str) else col_or_name
    return Column(c.expr.exp())


def log(col_or_name: Union[str, Column], base: float = 2.718281828459045) -> Column:
    """Logarithm."""
    c = Column(col_or_name) if isinstance(col_or_name, str) else col_or_name
    return Column(c.expr.log(base))


def log10(col_or_name: Union[str, Column]) -> Column:
    """Log base 10."""
    c = Column(col_or_name) if isinstance(col_or_name, str) else col_or_name
    return Column(c.expr.log(10))


def log2(col_or_name: Union[str, Column]) -> Column:
    """Log base 2."""
    c = Column(col_or_name) if isinstance(col_or_name, str) else col_or_name
    return Column(c.expr.log(2))


def pow(col1: Union[str, Column], col2: Union[str, Column, float]) -> Column:
    """Power function."""
    c1 = Column(col1) if isinstance(col1, str) else col1
    if isinstance(col2, (int, float)):
        return Column(c1.expr.pow(col2))
    c2 = Column(col2) if isinstance(col2, str) else col2
    return Column(c1.expr.pow(c2.expr))


def floor(col_or_name: Union[str, Column]) -> Column:
    """Floor value."""
    c = Column(col_or_name) if isinstance(col_or_name, str) else col_or_name
    return Column(c.expr.floor())


def ceil(col_or_name: Union[str, Column]) -> Column:
    """Ceiling value."""
    c = Column(col_or_name) if isinstance(col_or_name, str) else col_or_name
    return Column(c.expr.ceil())


def round(col_or_name: Union[str, Column], scale: int = 0) -> Column:
    """Round value."""
    c = Column(col_or_name) if isinstance(col_or_name, str) else col_or_name
    return Column(c.expr.round(scale))


def sin(col_or_name: Union[str, Column]) -> Column:
    """Sine."""
    c = Column(col_or_name) if isinstance(col_or_name, str) else col_or_name
    return Column(c.expr.sin())


def cos(col_or_name: Union[str, Column]) -> Column:
    """Cosine."""
    c = Column(col_or_name) if isinstance(col_or_name, str) else col_or_name
    return Column(c.expr.cos())


def tan(col_or_name: Union[str, Column]) -> Column:
    """Tangent."""
    c = Column(col_or_name) if isinstance(col_or_name, str) else col_or_name
    return Column(c.expr.tan())


def rand(seed: Optional[int] = None) -> Column:
    """Random value between 0 and 1."""
    return Column(pl.lit(0).map_batches(lambda x: pl.Series([__import__('random').random() for _ in range(len(x))])))


def randn(seed: Optional[int] = None) -> Column:
    """Random value from normal distribution."""
    return Column(pl.lit(0).map_batches(lambda x: pl.Series([__import__('random').gauss(0, 1) for _ in range(len(x))])))


# ============================================================
# Array Functions
# ============================================================

def array(*cols: Union[str, Column]) -> Column:
    """Creates an array column."""
    exprs = [Column(c).expr if isinstance(c, str) else c.expr for c in cols]
    return Column(pl.concat_list(exprs))


def array_contains(col_or_name: Union[str, Column], value: Any) -> Column:
    """Check if array contains value."""
    c = Column(col_or_name) if isinstance(col_or_name, str) else col_or_name
    return Column(c.expr.list.contains(value))


def array_size(col_or_name: Union[str, Column]) -> Column:
    """Get array size."""
    c = Column(col_or_name) if isinstance(col_or_name, str) else col_or_name
    return Column(c.expr.list.len())


def explode(col_or_name: Union[str, Column]) -> Column:
    """Explode array into rows."""
    c = Column(col_or_name) if isinstance(col_or_name, str) else col_or_name
    return Column(c.expr.explode())


def explode_outer(col_or_name: Union[str, Column]) -> Column:
    """Explode array into rows, keeping nulls."""
    c = Column(col_or_name) if isinstance(col_or_name, str) else col_or_name
    return Column(c.expr.explode())


def flatten(col_or_name: Union[str, Column]) -> Column:
    """Flatten nested arrays."""
    c = Column(col_or_name) if isinstance(col_or_name, str) else col_or_name
    return Column(c.expr.list.explode())


# ============================================================
# Struct Functions
# ============================================================

def struct(*cols: Union[str, Column]) -> Column:
    """Creates a struct column."""
    exprs = [Column(c).expr if isinstance(c, str) else c.expr for c in cols]
    return Column(pl.struct(exprs))


# ============================================================
# Other Utility Functions
# ============================================================

def monotonically_increasing_id() -> Column:
    """Returns monotonically increasing 64-bit integers."""
    return Column(pl.int_range(pl.len(), dtype=pl.Int64))


def spark_partition_id() -> Column:
    """Returns the partition ID."""
    # In mock, we just return 0 as we don't have real partitions
    return Column(pl.lit(0))


def input_file_name() -> Column:
    """Returns the source file name."""
    return Column(pl.lit("mock_input"))


def expr(sql_expr: str) -> Column:
    """Parses the expression string into a Column."""
    # Simple expression parser - handles basic cases
    import re
    
    # Handle column reference
    if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', sql_expr):
        return col(sql_expr)
    
    # For more complex expressions, we would need a proper parser
    # This is a simplified version
    return col(sql_expr)


def broadcast(df: "DataFrame") -> "DataFrame":
    """Mark a DataFrame for broadcast join."""
    # In mock, this is a no-op but we track it for explain
    df._broadcast = True
    return df
