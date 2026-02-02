"""
Row class - represents a row in a DataFrame.
"""
from typing import Any, Dict, List, Optional, Tuple


class Row:
    """
    A row in a DataFrame.
    
    Supports attribute access, index access, and dictionary-like access.
    
    Example:
        row = Row(name="Alice", age=30)
        row.name  # "Alice"
        row["age"]  # 30
        row[0]  # "Alice" (by position)
    """
    
    __slots__ = ("_fields", "_values")
    
    def __init__(self, *args, **kwargs):
        if args and kwargs:
            raise ValueError("Cannot use both positional and keyword arguments")
        
        if args:
            # Positional arguments - no field names
            self._fields: Optional[Tuple[str, ...]] = None
            self._values: Tuple[Any, ...] = tuple(args)
        else:
            # Keyword arguments - with field names
            self._fields = tuple(kwargs.keys())
            self._values = tuple(kwargs.values())
    
    def __repr__(self) -> str:
        if self._fields:
            pairs = [f"{k}={repr(v)}" for k, v in zip(self._fields, self._values)]
            return f"Row({', '.join(pairs)})"
        else:
            return f"Row({', '.join(repr(v) for v in self._values)})"
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Row):
            return False
        return self._values == other._values
    
    def __hash__(self) -> int:
        return hash(self._values)
    
    def __len__(self) -> int:
        return len(self._values)
    
    def __getitem__(self, key):
        if isinstance(key, int):
            return self._values[key]
        elif isinstance(key, str):
            if self._fields is None:
                raise KeyError(f"Row has no named fields")
            try:
                idx = self._fields.index(key)
                return self._values[idx]
            except ValueError:
                raise KeyError(f"Field '{key}' not found")
        else:
            raise TypeError(f"Row indices must be int or str, not {type(key)}")
    
    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
    
    def __contains__(self, item) -> bool:
        return item in self._values or (self._fields and item in self._fields)
    
    def __iter__(self):
        return iter(self._values)
    
    def asDict(self, recursive: bool = False) -> Dict[str, Any]:
        """Return as a dictionary."""
        if self._fields is None:
            return {str(i): v for i, v in enumerate(self._values)}
        
        result = dict(zip(self._fields, self._values))
        
        if recursive:
            for k, v in result.items():
                if isinstance(v, Row):
                    result[k] = v.asDict(recursive=True)
                elif isinstance(v, list):
                    result[k] = [
                        item.asDict(recursive=True) if isinstance(item, Row) else item
                        for item in v
                    ]
        
        return result
    
    @classmethod
    def fromDict(cls, d: Dict[str, Any]) -> "Row":
        """Create a Row from a dictionary."""
        return cls(**d)
    
    def __reduce__(self):
        """Support pickling."""
        if self._fields:
            return (Row, (), {"_fields": self._fields, "_values": self._values})
        return (Row, self._values)
    
    def __setstate__(self, state):
        if isinstance(state, dict):
            object.__setattr__(self, "_fields", state["_fields"])
            object.__setattr__(self, "_values", state["_values"])
        else:
            object.__setattr__(self, "_fields", None)
            object.__setattr__(self, "_values", state)
