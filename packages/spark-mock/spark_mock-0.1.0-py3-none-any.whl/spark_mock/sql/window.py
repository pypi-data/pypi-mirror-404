"""
Window Functions - support for window operations.
"""
from typing import List, Optional, Union
import polars as pl
from spark_mock.sql.column import Column


class WindowSpec:
    """
    Window specification for window functions.
    
    Example:
        window = Window.partitionBy("department").orderBy("salary")
        df.withColumn("rank", F.rank().over(window))
    """
    
    def __init__(self):
        self._partition_by: List[str] = []
        self._order_by: List[str] = []
        self._order_desc: List[bool] = []
        self._rows_between: Optional[tuple] = None
        self._range_between: Optional[tuple] = None
    
    def partitionBy(self, *cols: Union[str, Column]) -> "WindowSpec":
        """Define partition columns."""
        new_spec = WindowSpec()
        new_spec._partition_by = [
            c if isinstance(c, str) else str(c) for c in cols
        ]
        new_spec._order_by = self._order_by.copy()
        new_spec._order_desc = self._order_desc.copy()
        return new_spec
    
    def orderBy(self, *cols: Union[str, Column]) -> "WindowSpec":
        """Define ordering columns."""
        new_spec = WindowSpec()
        new_spec._partition_by = self._partition_by.copy()
        new_spec._order_by = []
        new_spec._order_desc = []
        
        for c in cols:
            if isinstance(c, str):
                new_spec._order_by.append(c)
                new_spec._order_desc.append(False)
            elif isinstance(c, Column):
                new_spec._order_by.append(str(c))
                new_spec._order_desc.append(False)
        
        return new_spec
    
    def rowsBetween(self, start: int, end: int) -> "WindowSpec":
        """Define window frame by rows."""
        new_spec = WindowSpec()
        new_spec._partition_by = self._partition_by.copy()
        new_spec._order_by = self._order_by.copy()
        new_spec._order_desc = self._order_desc.copy()
        new_spec._rows_between = (start, end)
        return new_spec
    
    def rangeBetween(self, start: int, end: int) -> "WindowSpec":
        """Define window frame by range."""
        new_spec = WindowSpec()
        new_spec._partition_by = self._partition_by.copy()
        new_spec._order_by = self._order_by.copy()
        new_spec._order_desc = self._order_desc.copy()
        new_spec._range_between = (start, end)
        return new_spec


class Window:
    """
    Factory for WindowSpec.
    
    Usage:
        Window.partitionBy("col1", "col2")
        Window.orderBy("col1")
        Window.partitionBy("col1").orderBy("col2")
    """
    
    # Unbounded constants
    unboundedPreceding = float("-inf")
    unboundedFollowing = float("inf")
    currentRow = 0
    
    @staticmethod
    def partitionBy(*cols: Union[str, Column]) -> WindowSpec:
        """Create a WindowSpec with partition columns."""
        return WindowSpec().partitionBy(*cols)
    
    @staticmethod
    def orderBy(*cols: Union[str, Column]) -> WindowSpec:
        """Create a WindowSpec with ordering columns."""
        return WindowSpec().orderBy(*cols)
    
    @staticmethod
    def rowsBetween(start: int, end: int) -> WindowSpec:
        """Create a WindowSpec with row-based frame."""
        return WindowSpec().rowsBetween(start, end)
    
    @staticmethod
    def rangeBetween(start: int, end: int) -> WindowSpec:
        """Create a WindowSpec with range-based frame."""
        return WindowSpec().rangeBetween(start, end)


# Window functions
def row_number() -> Column:
    """Returns a sequential number starting at 1 within a window partition."""
    return Column(pl.int_range(1, pl.len() + 1))


def rank() -> Column:
    """Returns the rank within a window partition."""
    return Column(pl.lit(1).rank("ordinal"))


def dense_rank() -> Column:
    """Returns the dense rank within a window partition."""
    return Column(pl.lit(1).rank("dense"))


def percent_rank() -> Column:
    """Returns the percentile rank within a window partition."""
    return Column(pl.lit(1).rank("ordinal") / pl.len())


def ntile(n: int) -> Column:
    """Divides rows into n groups and returns the group number."""
    return Column((pl.int_range(pl.len()) * n / pl.len()).floor().cast(pl.Int32) + 1)


def lag(col_or_name: Union[str, Column], offset: int = 1, default: Optional[any] = None) -> Column:
    """Returns the value offset rows before the current row."""
    from spark_mock.sql.column import Column as Col
    c = Col(col_or_name) if isinstance(col_or_name, str) else col_or_name
    if default is not None:
        return Column(c.expr.shift(offset).fill_null(default))
    return Column(c.expr.shift(offset))


def lead(col_or_name: Union[str, Column], offset: int = 1, default: Optional[any] = None) -> Column:
    """Returns the value offset rows after the current row."""
    from spark_mock.sql.column import Column as Col
    c = Col(col_or_name) if isinstance(col_or_name, str) else col_or_name
    if default is not None:
        return Column(c.expr.shift(-offset).fill_null(default))
    return Column(c.expr.shift(-offset))


def cume_dist() -> Column:
    """Returns cumulative distribution within a window partition."""
    return Column(pl.int_range(1, pl.len() + 1) / pl.len())
