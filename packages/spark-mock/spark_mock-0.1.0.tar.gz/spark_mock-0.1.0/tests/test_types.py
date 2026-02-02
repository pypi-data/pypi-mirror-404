"""
Unit tests for Data Types.
"""
import unittest
import polars as pl

from spark_mock.sql.types import (
    DataType, NullType, StringType, BinaryType,
    BooleanType, ByteType, ShortType, IntegerType, LongType,
    FloatType, DoubleType, DecimalType, DateType, TimestampType,
    ArrayType, MapType, StructField, StructType,
    _infer_schema
)


class TestPrimitiveTypes(unittest.TestCase):
    """Tests for primitive data types."""
    
    def test_string_type(self):
        """Test StringType."""
        t = StringType()
        self.assertEqual(t.simpleString(), "string")
        self.assertEqual(t.typeName(), "string")
    
    def test_integer_type(self):
        """Test IntegerType."""
        t = IntegerType()
        self.assertEqual(t.simpleString(), "int")
        self.assertEqual(t.typeName(), "integer")
    
    def test_long_type(self):
        """Test LongType."""
        t = LongType()
        self.assertEqual(t.simpleString(), "bigint")
    
    def test_double_type(self):
        """Test DoubleType."""
        t = DoubleType()
        self.assertEqual(t.simpleString(), "double")
    
    def test_float_type(self):
        """Test FloatType."""
        t = FloatType()
        self.assertEqual(t.simpleString(), "float")
    
    def test_boolean_type(self):
        """Test BooleanType."""
        t = BooleanType()
        self.assertEqual(t.simpleString(), "boolean")
    
    def test_date_type(self):
        """Test DateType."""
        t = DateType()
        self.assertEqual(t.simpleString(), "date")
    
    def test_timestamp_type(self):
        """Test TimestampType."""
        t = TimestampType()
        self.assertEqual(t.simpleString(), "timestamp")
    
    def test_null_type(self):
        """Test NullType."""
        t = NullType()
        self.assertEqual(t.simpleString(), "null")
    
    def test_binary_type(self):
        """Test BinaryType."""
        t = BinaryType()
        self.assertEqual(t.simpleString(), "binary")
    
    def test_byte_type(self):
        """Test ByteType."""
        t = ByteType()
        self.assertEqual(t.simpleString(), "tinyint")
    
    def test_short_type(self):
        """Test ShortType."""
        t = ShortType()
        self.assertEqual(t.simpleString(), "smallint")


class TestDecimalType(unittest.TestCase):
    """Tests for DecimalType."""
    
    def test_default_decimal(self):
        """Test default DecimalType."""
        t = DecimalType()
        self.assertEqual(t.precision, 10)
        self.assertEqual(t.scale, 0)
    
    def test_custom_decimal(self):
        """Test custom DecimalType."""
        t = DecimalType(18, 2)
        self.assertEqual(t.precision, 18)
        self.assertEqual(t.scale, 2)
    
    def test_decimal_string(self):
        """Test DecimalType string representation."""
        t = DecimalType(10, 2)
        self.assertEqual(t.simpleString(), "decimal(10,2)")


class TestArrayType(unittest.TestCase):
    """Tests for ArrayType."""
    
    def test_array_of_strings(self):
        """Test ArrayType with StringType."""
        t = ArrayType(StringType())
        self.assertEqual(t.simpleString(), "array<string>")
    
    def test_array_of_integers(self):
        """Test ArrayType with IntegerType."""
        t = ArrayType(IntegerType())
        self.assertEqual(t.simpleString(), "array<int>")
    
    def test_array_not_nullable(self):
        """Test ArrayType with containsNull=False."""
        t = ArrayType(StringType(), containsNull=False)
        self.assertFalse(t.containsNull)
    
    def test_nested_array(self):
        """Test nested ArrayType."""
        t = ArrayType(ArrayType(IntegerType()))
        self.assertEqual(t.simpleString(), "array<array<int>>")


class TestMapType(unittest.TestCase):
    """Tests for MapType."""
    
    def test_string_to_int_map(self):
        """Test MapType with string keys and int values."""
        t = MapType(StringType(), IntegerType())
        self.assertEqual(t.simpleString(), "map<string,int>")
    
    def test_map_not_nullable(self):
        """Test MapType with valueContainsNull=False."""
        t = MapType(StringType(), IntegerType(), valueContainsNull=False)
        self.assertFalse(t.valueContainsNull)


class TestStructField(unittest.TestCase):
    """Tests for StructField."""
    
    def test_basic_field(self):
        """Test basic StructField."""
        field = StructField("name", StringType(), True)
        self.assertEqual(field.name, "name")
        self.assertIsInstance(field.dataType, StringType)
        self.assertTrue(field.nullable)
    
    def test_not_nullable_field(self):
        """Test non-nullable StructField."""
        field = StructField("id", IntegerType(), False)
        self.assertFalse(field.nullable)
    
    def test_field_with_metadata(self):
        """Test StructField with metadata."""
        field = StructField("col", StringType(), True, {"comment": "test"})
        self.assertEqual(field.metadata, {"comment": "test"})


class TestStructType(unittest.TestCase):
    """Tests for StructType."""
    
    def test_empty_struct(self):
        """Test empty StructType."""
        schema = StructType()
        self.assertEqual(len(schema.fields), 0)
    
    def test_struct_with_fields(self):
        """Test StructType with fields."""
        schema = StructType([
            StructField("id", IntegerType(), False),
            StructField("name", StringType(), True)
        ])
        self.assertEqual(len(schema.fields), 2)
    
    def test_add_field(self):
        """Test adding field to StructType."""
        schema = StructType()
        schema.add("id", IntegerType(), False)
        self.assertEqual(len(schema.fields), 1)
    
    def test_field_names(self):
        """Test fieldNames property."""
        schema = StructType([
            StructField("a", IntegerType()),
            StructField("b", StringType())
        ])
        self.assertEqual(schema.fieldNames(), ["a", "b"])
    
    def test_names_property(self):
        """Test names property."""
        schema = StructType([
            StructField("x", IntegerType()),
            StructField("y", StringType())
        ])
        self.assertEqual(schema.names, ["x", "y"])
    
    def test_getitem_by_name(self):
        """Test accessing field by name."""
        schema = StructType([
            StructField("id", IntegerType()),
            StructField("name", StringType())
        ])
        self.assertEqual(schema["name"].name, "name")
    
    def test_getitem_by_index(self):
        """Test accessing field by index."""
        schema = StructType([
            StructField("id", IntegerType()),
            StructField("name", StringType())
        ])
        self.assertEqual(schema[0].name, "id")


if __name__ == "__main__":
    unittest.main()
