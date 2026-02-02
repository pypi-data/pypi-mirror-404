"""
Unit tests for SQL functions.
"""
import unittest
from datetime import date, datetime

from spark_mock.sql import SparkSession
from spark_mock.sql import functions as F
from spark_mock.sql.session import SparkContext


class TestAggregationFunctions(unittest.TestCase):
    """Tests for aggregation functions."""
    
    @classmethod
    def setUpClass(cls):
        SparkSession._active_session = None
        SparkContext._active_context = None
        cls.spark = SparkSession.builder \
            .config("spark.mock.ui.console", "false") \
            .getOrCreate()
        
        cls.df = cls.spark.createDataFrame([
            (1, 10),
            (2, 20),
            (3, 30),
            (4, 40),
        ], ["id", "value"])
    
    @classmethod
    def tearDownClass(cls):
        cls.spark.stop()
    
    def test_count(self):
        """Test count function."""
        result = self.df.select(F.count("*"))
        rows = result.collect()
        self.assertEqual(rows[0][0], 4)
    
    def test_sum(self):
        """Test sum function."""
        result = self.df.select(F.sum("value"))
        rows = result.collect()
        self.assertEqual(rows[0][0], 100)
    
    def test_avg(self):
        """Test avg function."""
        result = self.df.select(F.avg("value"))
        rows = result.collect()
        self.assertEqual(rows[0][0], 25.0)
    
    def test_mean(self):
        """Test mean function (alias for avg)."""
        result = self.df.select(F.mean("value"))
        rows = result.collect()
        self.assertEqual(rows[0][0], 25.0)
    
    def test_min(self):
        """Test min function."""
        result = self.df.select(F.min("value"))
        rows = result.collect()
        self.assertEqual(rows[0][0], 10)
    
    def test_max(self):
        """Test max function."""
        result = self.df.select(F.max("value"))
        rows = result.collect()
        self.assertEqual(rows[0][0], 40)
    
    def test_count_distinct(self):
        """Test countDistinct function."""
        df = self.spark.createDataFrame([
            (1, "a"), (2, "a"), (3, "b")
        ], ["id", "cat"])
        result = df.select(F.countDistinct("cat"))
        rows = result.collect()
        self.assertEqual(rows[0][0], 2)


class TestStringFunctions(unittest.TestCase):
    """Tests for string functions."""
    
    @classmethod
    def setUpClass(cls):
        SparkSession._active_session = None
        SparkContext._active_context = None
        cls.spark = SparkSession.builder \
            .config("spark.mock.ui.console", "false") \
            .getOrCreate()
        
        cls.df = cls.spark.createDataFrame([
            (1, "hello world"),
            (2, "UPPERCASE"),
            (3, "  trimme  "),
        ], ["id", "text"])
    
    @classmethod
    def tearDownClass(cls):
        cls.spark.stop()
    
    def test_concat(self):
        """Test concat function."""
        df = self.spark.createDataFrame([(1, "a", "b")], ["id", "c1", "c2"])
        result = df.select(F.concat(F.col("c1"), F.col("c2")))
        rows = result.collect()
        self.assertEqual(rows[0][0], "ab")
    
    def test_concat_ws(self):
        """Test concat_ws function."""
        df = self.spark.createDataFrame([(1, "a", "b", "c")], ["id", "c1", "c2", "c3"])
        result = df.select(F.concat_ws("-", F.col("c1"), F.col("c2"), F.col("c3")))
        rows = result.collect()
        self.assertEqual(rows[0][0], "a-b-c")
    
    def test_upper(self):
        """Test upper function."""
        result = self.df.filter(F.col("id") == 1).select(F.upper(F.col("text")))
        rows = result.collect()
        self.assertEqual(rows[0][0], "HELLO WORLD")
    
    def test_lower(self):
        """Test lower function."""
        result = self.df.filter(F.col("id") == 2).select(F.lower(F.col("text")))
        rows = result.collect()
        self.assertEqual(rows[0][0], "uppercase")
    
    def test_length(self):
        """Test length function."""
        result = self.df.filter(F.col("id") == 1).select(F.length(F.col("text")))
        rows = result.collect()
        self.assertEqual(rows[0][0], 11)  # "hello world"
    
    def test_trim(self):
        """Test trim function."""
        result = self.df.filter(F.col("id") == 3).select(F.trim(F.col("text")))
        rows = result.collect()
        self.assertEqual(rows[0][0], "trimme")
    
    def test_substring(self):
        """Test substring function."""
        result = self.df.filter(F.col("id") == 1).select(F.substring(F.col("text"), 1, 5))
        rows = result.collect()
        self.assertEqual(rows[0][0], "hello")
    
    def test_split(self):
        """Test split function."""
        result = self.df.filter(F.col("id") == 1).select(F.split(F.col("text"), " "))
        rows = result.collect()
        self.assertEqual(rows[0][0], ["hello", "world"])


class TestMathFunctions(unittest.TestCase):
    """Tests for math functions."""
    
    @classmethod
    def setUpClass(cls):
        SparkSession._active_session = None
        SparkContext._active_context = None
        cls.spark = SparkSession.builder \
            .config("spark.mock.ui.console", "false") \
            .getOrCreate()
        
        cls.df = cls.spark.createDataFrame([
            (1, -5.5, 4.0),
            (2, 10.3, 9.0),
        ], ["id", "a", "b"])
    
    @classmethod
    def tearDownClass(cls):
        cls.spark.stop()
    
    def test_abs(self):
        """Test abs function."""
        result = self.df.filter(F.col("id") == 1).select(F.abs(F.col("a")))
        rows = result.collect()
        self.assertEqual(rows[0][0], 5.5)
    
    def test_sqrt(self):
        """Test sqrt function."""
        result = self.df.filter(F.col("id") == 2).select(F.sqrt(F.col("b")))
        rows = result.collect()
        self.assertEqual(rows[0][0], 3.0)
    
    def test_round(self):
        """Test round function."""
        result = self.df.filter(F.col("id") == 2).select(F.round(F.col("a"), 0))
        rows = result.collect()
        self.assertEqual(rows[0][0], 10.0)
    
    def test_floor(self):
        """Test floor function."""
        result = self.df.filter(F.col("id") == 2).select(F.floor(F.col("a")))
        rows = result.collect()
        self.assertEqual(rows[0][0], 10)
    
    def test_ceil(self):
        """Test ceil function."""
        result = self.df.filter(F.col("id") == 2).select(F.ceil(F.col("a")))
        rows = result.collect()
        self.assertEqual(rows[0][0], 11)


class TestConditionalFunctions(unittest.TestCase):
    """Tests for conditional functions."""
    
    @classmethod
    def setUpClass(cls):
        SparkSession._active_session = None
        SparkContext._active_context = None
        cls.spark = SparkSession.builder \
            .config("spark.mock.ui.console", "false") \
            .getOrCreate()
        
        cls.df = cls.spark.createDataFrame([
            (1, 10, None),
            (2, None, 20),
            (3, 30, 40),
        ], ["id", "a", "b"])
    
    @classmethod
    def tearDownClass(cls):
        cls.spark.stop()
    
    def test_when_otherwise(self):
        """Test when/otherwise."""
        result = self.df.select(
            F.when(F.col("a").isNull(), "null")
             .otherwise("not_null")
             .alias("result")
        )
        rows = result.collect()
        self.assertEqual(rows[0]["result"], "not_null")  # id=1
        self.assertEqual(rows[1]["result"], "null")       # id=2
    
    def test_coalesce(self):
        """Test coalesce function."""
        result = self.df.select(F.coalesce(F.col("a"), F.col("b")).alias("result"))
        rows = result.collect()
        self.assertEqual(rows[0]["result"], 10)  # id=1, a not null
        self.assertEqual(rows[1]["result"], 20)  # id=2, a null, b=20
    
    def test_isnull(self):
        """Test isnull function."""
        result = self.df.select(F.isnull(F.col("a")).alias("is_null"))
        rows = result.collect()
        self.assertFalse(rows[0]["is_null"])  # id=1
        self.assertTrue(rows[1]["is_null"])   # id=2


class TestLiteralFunctions(unittest.TestCase):
    """Tests for literal and utility functions."""
    
    @classmethod
    def setUpClass(cls):
        SparkSession._active_session = None
        SparkContext._active_context = None
        cls.spark = SparkSession.builder \
            .config("spark.mock.ui.console", "false") \
            .getOrCreate()
    
    @classmethod
    def tearDownClass(cls):
        cls.spark.stop()
    
    def test_lit_int(self):
        """Test lit with integer."""
        df = self.spark.createDataFrame([(1,)], ["id"])
        result = df.select(F.lit(42).alias("value"))
        rows = result.collect()
        self.assertEqual(rows[0]["value"], 42)
    
    def test_lit_string(self):
        """Test lit with string."""
        df = self.spark.createDataFrame([(1,)], ["id"])
        result = df.select(F.lit("hello").alias("value"))
        rows = result.collect()
        self.assertEqual(rows[0]["value"], "hello")
    
    def test_col(self):
        """Test col function."""
        df = self.spark.createDataFrame([(1, "test")], ["id", "name"])
        result = df.select(F.col("name"))
        self.assertEqual(result.columns, ["name"])


if __name__ == "__main__":
    unittest.main()
