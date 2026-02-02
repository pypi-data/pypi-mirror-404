"""
Spark SQL Data Types - mirrors pyspark.sql.types
"""
from typing import List, Optional, Any
from dataclasses import dataclass
import polars as pl


class DataType:
    """Base class for all data types."""
    
    def simpleString(self) -> str:
        return self.__class__.__name__.lower().replace("type", "")
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"
    
    def to_polars(self) -> pl.DataType:
        """Convert to Polars data type."""
        raise NotImplementedError


class NullType(DataType):
    def to_polars(self) -> pl.DataType:
        return pl.Null


class StringType(DataType):
    def to_polars(self) -> pl.DataType:
        return pl.Utf8


class BinaryType(DataType):
    def to_polars(self) -> pl.DataType:
        return pl.Binary


class BooleanType(DataType):
    def to_polars(self) -> pl.DataType:
        return pl.Boolean


class DateType(DataType):
    def to_polars(self) -> pl.DataType:
        return pl.Date


class TimestampType(DataType):
    def to_polars(self) -> pl.DataType:
        return pl.Datetime


class DecimalType(DataType):
    def __init__(self, precision: int = 10, scale: int = 0):
        self.precision = precision
        self.scale = scale
    
    def __repr__(self) -> str:
        return f"DecimalType({self.precision}, {self.scale})"
    
    def to_polars(self) -> pl.DataType:
        return pl.Decimal(precision=self.precision, scale=self.scale)


class DoubleType(DataType):
    def to_polars(self) -> pl.DataType:
        return pl.Float64


class FloatType(DataType):
    def to_polars(self) -> pl.DataType:
        return pl.Float32


class ByteType(DataType):
    def to_polars(self) -> pl.DataType:
        return pl.Int8


class IntegerType(DataType):
    def to_polars(self) -> pl.DataType:
        return pl.Int32


class LongType(DataType):
    def to_polars(self) -> pl.DataType:
        return pl.Int64


class ShortType(DataType):
    def to_polars(self) -> pl.DataType:
        return pl.Int16


class ArrayType(DataType):
    def __init__(self, elementType: DataType, containsNull: bool = True):
        self.elementType = elementType
        self.containsNull = containsNull
    
    def __repr__(self) -> str:
        return f"ArrayType({self.elementType}, {self.containsNull})"
    
    def to_polars(self) -> pl.DataType:
        return pl.List(self.elementType.to_polars())


class MapType(DataType):
    def __init__(self, keyType: DataType, valueType: DataType, valueContainsNull: bool = True):
        self.keyType = keyType
        self.valueType = valueType
        self.valueContainsNull = valueContainsNull
    
    def __repr__(self) -> str:
        return f"MapType({self.keyType}, {self.valueType}, {self.valueContainsNull})"
    
    def to_polars(self) -> pl.DataType:
        # Polars doesn't have a direct Map type, use Struct as approximation
        return pl.Struct([
            pl.Field("key", self.keyType.to_polars()),
            pl.Field("value", self.valueType.to_polars())
        ])


@dataclass
class StructField:
    """A field in a StructType."""
    name: str
    dataType: DataType
    nullable: bool = True
    metadata: Optional[dict] = None
    
    def __repr__(self) -> str:
        return f"StructField('{self.name}', {self.dataType}, {self.nullable})"


class StructType(DataType):
    """Schema for a DataFrame."""
    
    def __init__(self, fields: Optional[List[StructField]] = None):
        self.fields = fields or []
    
    def add(self, field: str | StructField, data_type: Optional[DataType] = None, 
            nullable: bool = True, metadata: Optional[dict] = None) -> "StructType":
        """Add a field to the schema."""
        if isinstance(field, StructField):
            self.fields.append(field)
        else:
            self.fields.append(StructField(field, data_type, nullable, metadata))
        return self
    
    def __iter__(self):
        return iter(self.fields)
    
    def __len__(self):
        return len(self.fields)
    
    def __getitem__(self, key):
        if isinstance(key, int):
            return self.fields[key]
        for field in self.fields:
            if field.name == key:
                return field
        raise KeyError(f"Field '{key}' not found")
    
    @property
    def names(self) -> List[str]:
        return [f.name for f in self.fields]
    
    def to_polars(self) -> pl.Schema:
        """Convert to Polars schema."""
        return {f.name: f.dataType.to_polars() for f in self.fields}
    
    def simpleString(self) -> str:
        return f"struct<{', '.join(f'{f.name}:{f.dataType.simpleString()}' for f in self.fields)}>"
    
    def __repr__(self) -> str:
        fields_str = ",\n    ".join(repr(f) for f in self.fields)
        return f"StructType([\n    {fields_str}\n])"


# Type mapping from string to DataType
_TYPE_MAPPINGS = {
    "string": StringType(),
    "str": StringType(),
    "int": IntegerType(),
    "integer": IntegerType(),
    "long": LongType(),
    "bigint": LongType(),
    "float": FloatType(),
    "double": DoubleType(),
    "boolean": BooleanType(),
    "bool": BooleanType(),
    "date": DateType(),
    "timestamp": TimestampType(),
    "binary": BinaryType(),
    "byte": ByteType(),
    "short": ShortType(),
}


def _parse_type(type_str: str) -> DataType:
    """Parse a type string to DataType."""
    type_str = type_str.lower().strip()
    if type_str in _TYPE_MAPPINGS:
        return _TYPE_MAPPINGS[type_str]
    raise ValueError(f"Unknown type: {type_str}")


def _infer_type(value: Any) -> DataType:
    """Infer DataType from a Python value."""
    if value is None:
        return NullType()
    elif isinstance(value, bool):
        return BooleanType()
    elif isinstance(value, int):
        return LongType()
    elif isinstance(value, float):
        return DoubleType()
    elif isinstance(value, str):
        return StringType()
    elif isinstance(value, bytes):
        return BinaryType()
    elif isinstance(value, list):
        if len(value) > 0:
            return ArrayType(_infer_type(value[0]))
        return ArrayType(StringType())
    elif isinstance(value, dict):
        return MapType(StringType(), StringType())
    else:
        return StringType()


def _infer_schema(data: List[tuple], columns: List[str]) -> StructType:
    """Infer schema from data."""
    if not data:
        return StructType([StructField(col, StringType()) for col in columns])
    
    first_row = data[0]
    fields = []
    for i, col in enumerate(columns):
        value = first_row[i] if i < len(first_row) else None
        fields.append(StructField(col, _infer_type(value)))
    return StructType(fields)
