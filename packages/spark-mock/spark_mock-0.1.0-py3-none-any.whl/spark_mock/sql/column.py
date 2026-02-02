"""
Column class - represents a column expression in a DataFrame.
"""
from typing import Any, Optional, Union, List, TYPE_CHECKING
import polars as pl

if TYPE_CHECKING:
    from spark_mock.sql.dataframe import DataFrame


class Column:
    """
    A column in a DataFrame.
    
    Supports operations like:
    - Arithmetic: +, -, *, /, %
    - Comparison: ==, !=, <, <=, >, >=
    - Logical: &, |, ~
    - String: like, startswith, endswith, contains
    - Null handling: isNull, isNotNull
    - Casting: cast
    - Aliasing: alias
    """
    
    def __init__(self, expr: Union[str, pl.Expr]):
        if isinstance(expr, str):
            self._expr = pl.col(expr)
            self._name = expr
        elif isinstance(expr, pl.Expr):
            self._expr = expr
            self._name = None
        else:
            raise TypeError(f"Column expects str or pl.Expr, got {type(expr)}")
    
    @property
    def expr(self) -> pl.Expr:
        """Get the underlying Polars expression."""
        return self._expr
    
    def __repr__(self) -> str:
        return f"Column<{self._name or 'expr'}>"
    
    def __str__(self) -> str:
        return self._name or str(self._expr)
    
    # Arithmetic operations
    def __add__(self, other: Union["Column", Any]) -> "Column":
        other_expr = other._expr if isinstance(other, Column) else pl.lit(other)
        return Column(self._expr + other_expr)
    
    def __radd__(self, other: Any) -> "Column":
        return Column(pl.lit(other) + self._expr)
    
    def __sub__(self, other: Union["Column", Any]) -> "Column":
        other_expr = other._expr if isinstance(other, Column) else pl.lit(other)
        return Column(self._expr - other_expr)
    
    def __rsub__(self, other: Any) -> "Column":
        return Column(pl.lit(other) - self._expr)
    
    def __mul__(self, other: Union["Column", Any]) -> "Column":
        other_expr = other._expr if isinstance(other, Column) else pl.lit(other)
        return Column(self._expr * other_expr)
    
    def __rmul__(self, other: Any) -> "Column":
        return Column(pl.lit(other) * self._expr)
    
    def __truediv__(self, other: Union["Column", Any]) -> "Column":
        other_expr = other._expr if isinstance(other, Column) else pl.lit(other)
        return Column(self._expr / other_expr)
    
    def __rtruediv__(self, other: Any) -> "Column":
        return Column(pl.lit(other) / self._expr)
    
    def __mod__(self, other: Union["Column", Any]) -> "Column":
        other_expr = other._expr if isinstance(other, Column) else pl.lit(other)
        return Column(self._expr % other_expr)
    
    def __neg__(self) -> "Column":
        return Column(-self._expr)
    
    # Comparison operations
    def __eq__(self, other: Union["Column", Any]) -> "Column":
        other_expr = other._expr if isinstance(other, Column) else pl.lit(other)
        return Column(self._expr == other_expr)
    
    def __ne__(self, other: Union["Column", Any]) -> "Column":
        other_expr = other._expr if isinstance(other, Column) else pl.lit(other)
        return Column(self._expr != other_expr)
    
    def __lt__(self, other: Union["Column", Any]) -> "Column":
        other_expr = other._expr if isinstance(other, Column) else pl.lit(other)
        return Column(self._expr < other_expr)
    
    def __le__(self, other: Union["Column", Any]) -> "Column":
        other_expr = other._expr if isinstance(other, Column) else pl.lit(other)
        return Column(self._expr <= other_expr)
    
    def __gt__(self, other: Union["Column", Any]) -> "Column":
        other_expr = other._expr if isinstance(other, Column) else pl.lit(other)
        return Column(self._expr > other_expr)
    
    def __ge__(self, other: Union["Column", Any]) -> "Column":
        other_expr = other._expr if isinstance(other, Column) else pl.lit(other)
        return Column(self._expr >= other_expr)
    
    # Logical operations
    def __and__(self, other: "Column") -> "Column":
        return Column(self._expr & other._expr)
    
    def __or__(self, other: "Column") -> "Column":
        return Column(self._expr | other._expr)
    
    def __invert__(self) -> "Column":
        return Column(~self._expr)
    
    # String operations
    def like(self, pattern: str) -> "Column":
        """SQL LIKE pattern matching."""
        # Convert SQL LIKE pattern to regex
        regex = pattern.replace("%", ".*").replace("_", ".")
        return Column(self._expr.str.contains(f"^{regex}$"))
    
    def rlike(self, pattern: str) -> "Column":
        """Regex pattern matching."""
        return Column(self._expr.str.contains(pattern))
    
    def startswith(self, prefix: Union[str, "Column"]) -> "Column":
        """String starts with prefix."""
        if isinstance(prefix, Column):
            # For column comparison, use expr
            return Column(self._expr.str.starts_with(prefix._expr))
        return Column(self._expr.str.starts_with(prefix))
    
    def endswith(self, suffix: Union[str, "Column"]) -> "Column":
        """String ends with suffix."""
        if isinstance(suffix, Column):
            return Column(self._expr.str.ends_with(suffix._expr))
        return Column(self._expr.str.ends_with(suffix))
    
    def contains(self, pattern: str) -> "Column":
        """String contains pattern."""
        return Column(self._expr.str.contains(pattern, literal=True))
    
    def substr(self, start: int, length: int) -> "Column":
        """Extract substring."""
        return Column(self._expr.str.slice(start - 1, length))  # Spark is 1-indexed
    
    def lower(self) -> "Column":
        """Convert to lowercase."""
        return Column(self._expr.str.to_lowercase())
    
    def upper(self) -> "Column":
        """Convert to uppercase."""
        return Column(self._expr.str.to_uppercase())
    
    def trim(self) -> "Column":
        """Trim whitespace."""
        return Column(self._expr.str.strip_chars())
    
    def ltrim(self) -> "Column":
        """Left trim."""
        return Column(self._expr.str.strip_chars_start())
    
    def rtrim(self) -> "Column":
        """Right trim."""
        return Column(self._expr.str.strip_chars_end())
    
    def length(self) -> "Column":
        """String length."""
        return Column(self._expr.str.len_chars())
    
    # Null handling
    def isNull(self) -> "Column":
        """Check if null."""
        return Column(self._expr.is_null())
    
    def isNotNull(self) -> "Column":
        """Check if not null."""
        return Column(self._expr.is_not_null())
    
    def isNaN(self) -> "Column":
        """Check if NaN."""
        return Column(self._expr.is_nan())
    
    # Type casting
    def cast(self, dataType: Union[str, "DataType"]) -> "Column":
        """Cast to another type."""
        from spark_mock.sql.types import _parse_type, DataType
        
        if isinstance(dataType, str):
            dt = _parse_type(dataType)
        else:
            dt = dataType
        
        return Column(self._expr.cast(dt.to_polars()))
    
    def astype(self, dataType: Union[str, "DataType"]) -> "Column":
        """Alias for cast."""
        return self.cast(dataType)
    
    # Aggregation (returns Column for use in agg)
    def _agg(self, func_name: str) -> "Column":
        """Helper for aggregation functions."""
        func = getattr(self._expr, func_name)
        return Column(func())
    
    # Aliasing
    def alias(self, name: str) -> "Column":
        """Give the column an alias."""
        col = Column(self._expr.alias(name))
        col._name = name
        return col
    
    def name(self, name: str) -> "Column":
        """Alias for alias."""
        return self.alias(name)
    
    # Sorting
    def asc(self) -> "Column":
        """Sort ascending."""
        return Column(self._expr.sort(descending=False))
    
    def desc(self) -> "Column":
        """Sort descending."""
        return Column(self._expr.sort(descending=True))
    
    def asc_nulls_first(self) -> "Column":
        """Sort ascending with nulls first."""
        return Column(self._expr.sort(descending=False, nulls_last=False))
    
    def asc_nulls_last(self) -> "Column":
        """Sort ascending with nulls last."""
        return Column(self._expr.sort(descending=False, nulls_last=True))
    
    def desc_nulls_first(self) -> "Column":
        """Sort descending with nulls first."""
        return Column(self._expr.sort(descending=True, nulls_last=False))
    
    def desc_nulls_last(self) -> "Column":
        """Sort descending with nulls last."""
        return Column(self._expr.sort(descending=True, nulls_last=True))
    
    # Other operations
    def between(self, lower: Any, upper: Any) -> "Column":
        """Check if value is between lower and upper (inclusive)."""
        return (self >= lower) & (self <= upper)
    
    def isin(self, *values) -> "Column":
        """Check if value is in a list of values."""
        if len(values) == 1 and isinstance(values[0], (list, tuple)):
            values = values[0]
        return Column(self._expr.is_in(list(values)))
    
    def otherwise(self, value: Any) -> "Column":
        """For use with when().otherwise()."""
        # This is handled specially in the when() function
        other_expr = value._expr if isinstance(value, Column) else pl.lit(value)
        return Column(self._expr.otherwise(other_expr))
    
    def over(self, window) -> "Column":
        """Apply window function."""
        from spark_mock.sql.window import WindowSpec
        if isinstance(window, WindowSpec):
            return Column(self._expr.over(window._partition_by))
        return self
    
    # Fill null
    def fillna(self, value: Any) -> "Column":
        """Fill null values."""
        fill_val = value._expr if isinstance(value, Column) else value
        return Column(self._expr.fill_null(fill_val))
    
    def coalesce(self, *cols) -> "Column":
        """Return first non-null value."""
        exprs = [self._expr] + [c._expr if isinstance(c, Column) else pl.lit(c) for c in cols]
        return Column(pl.coalesce(exprs))


def _to_column(item: Union[str, Column, pl.Expr]) -> Column:
    """Convert item to Column."""
    if isinstance(item, Column):
        return item
    elif isinstance(item, str):
        return Column(item)
    elif isinstance(item, pl.Expr):
        return Column(item)
    else:
        return Column(pl.lit(item))
