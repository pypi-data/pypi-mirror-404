"""
Unit tests for Column class.
"""
import unittest

from spark_mock.sql import SparkSession
from spark_mock.sql import functions as F
from spark_mock.sql.column import Column
from spark_mock.sql.session import SparkContext


class TestColumnCreation(unittest.TestCase):
    """Tests for Column creation."""
    
    def test_col_function(self):
        """Test creating column with col()."""
        col = F.col("name")
        self.assertIsInstance(col, Column)
    
    def test_lit_function(self):
        """Test creating literal column."""
        col = F.lit(42)
        self.assertIsInstance(col, Column)
    
    def test_column_name(self):
        """Test column name property."""
        col = F.col("age")
        self.assertEqual(col._name, "age")


class TestColumnArithmetic(unittest.TestCase):
    """Tests for Column arithmetic operations."""
    
    @classmethod
    def setUpClass(cls):
        SparkSession._active_session = None
        SparkContext._active_context = None
        cls.spark = SparkSession.builder \
            .config("spark.mock.ui.console", "false") \
            .getOrCreate()
        
        cls.df = cls.spark.createDataFrame([
            (1, 10, 2),
            (2, 20, 4),
            (3, 30, 5),
        ], ["id", "a", "b"])
    
    @classmethod
    def tearDownClass(cls):
        cls.spark.stop()
    
    def test_addition(self):
        """Test column addition."""
        result = self.df.withColumn("sum", F.col("a") + F.col("b"))
        rows = result.collect()
        self.assertEqual(rows[0]["sum"], 12)  # 10 + 2
    
    def test_subtraction(self):
        """Test column subtraction."""
        result = self.df.withColumn("diff", F.col("a") - F.col("b"))
        rows = result.collect()
        self.assertEqual(rows[0]["diff"], 8)  # 10 - 2
    
    def test_multiplication(self):
        """Test column multiplication."""
        result = self.df.withColumn("prod", F.col("a") * F.col("b"))
        rows = result.collect()
        self.assertEqual(rows[0]["prod"], 20)  # 10 * 2
    
    def test_division(self):
        """Test column division."""
        result = self.df.withColumn("quot", F.col("a") / F.col("b"))
        rows = result.collect()
        self.assertEqual(rows[0]["quot"], 5.0)  # 10 / 2
    
    def test_scalar_addition(self):
        """Test adding scalar to column."""
        result = self.df.withColumn("plus10", F.col("a") + 10)
        rows = result.collect()
        self.assertEqual(rows[0]["plus10"], 20)  # 10 + 10
    
    def test_scalar_multiplication(self):
        """Test multiplying column by scalar."""
        result = self.df.withColumn("double", F.col("a") * 2)
        rows = result.collect()
        self.assertEqual(rows[0]["double"], 20)  # 10 * 2
    
    def test_negation(self):
        """Test column negation."""
        result = self.df.withColumn("neg", -F.col("a"))
        rows = result.collect()
        self.assertEqual(rows[0]["neg"], -10)


class TestColumnComparison(unittest.TestCase):
    """Tests for Column comparison operations."""
    
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
        ], ["id", "value"])
    
    @classmethod
    def tearDownClass(cls):
        cls.spark.stop()
    
    def test_greater_than(self):
        """Test greater than comparison."""
        result = self.df.filter(F.col("value") > 15)
        self.assertEqual(result.count(), 2)
    
    def test_greater_than_or_equal(self):
        """Test greater than or equal."""
        result = self.df.filter(F.col("value") >= 20)
        self.assertEqual(result.count(), 2)
    
    def test_less_than(self):
        """Test less than comparison."""
        result = self.df.filter(F.col("value") < 25)
        self.assertEqual(result.count(), 2)
    
    def test_less_than_or_equal(self):
        """Test less than or equal."""
        result = self.df.filter(F.col("value") <= 20)
        self.assertEqual(result.count(), 2)
    
    def test_equals(self):
        """Test equals comparison."""
        result = self.df.filter(F.col("value") == 20)
        self.assertEqual(result.count(), 1)
    
    def test_not_equals(self):
        """Test not equals comparison."""
        result = self.df.filter(F.col("value") != 20)
        self.assertEqual(result.count(), 2)


class TestColumnLogical(unittest.TestCase):
    """Tests for Column logical operations."""
    
    @classmethod
    def setUpClass(cls):
        SparkSession._active_session = None
        SparkContext._active_context = None
        cls.spark = SparkSession.builder \
            .config("spark.mock.ui.console", "false") \
            .getOrCreate()
        
        cls.df = cls.spark.createDataFrame([
            (1, 10, True),
            (2, 20, False),
            (3, 30, True),
        ], ["id", "value", "flag"])
    
    @classmethod
    def tearDownClass(cls):
        cls.spark.stop()
    
    def test_and_operator(self):
        """Test AND operator."""
        result = self.df.filter((F.col("value") > 15) & (F.col("flag") == True))
        self.assertEqual(result.count(), 1)  # Only id=3
    
    def test_or_operator(self):
        """Test OR operator."""
        result = self.df.filter((F.col("value") < 15) | (F.col("value") > 25))
        self.assertEqual(result.count(), 2)  # id=1 and id=3
    
    def test_not_operator(self):
        """Test NOT operator."""
        result = self.df.filter(~(F.col("flag") == True))
        self.assertEqual(result.count(), 1)  # Only id=2


class TestColumnString(unittest.TestCase):
    """Tests for Column string operations."""
    
    @classmethod
    def setUpClass(cls):
        SparkSession._active_session = None
        SparkContext._active_context = None
        cls.spark = SparkSession.builder \
            .config("spark.mock.ui.console", "false") \
            .getOrCreate()
        
        cls.df = cls.spark.createDataFrame([
            (1, "Alice"),
            (2, "Bob"),
            (3, "Charlie"),
        ], ["id", "name"])
    
    @classmethod
    def tearDownClass(cls):
        cls.spark.stop()
    
    def test_contains(self):
        """Test contains method."""
        result = self.df.filter(F.col("name").contains("li"))
        self.assertEqual(result.count(), 2)  # Alice, Charlie
    
    def test_startswith(self):
        """Test startswith method."""
        result = self.df.filter(F.col("name").startswith("A"))
        self.assertEqual(result.count(), 1)  # Alice
    
    def test_endswith(self):
        """Test endswith method."""
        result = self.df.filter(F.col("name").endswith("e"))
        self.assertEqual(result.count(), 2)  # Alice, Charlie
    
    def test_like(self):
        """Test like method."""
        result = self.df.filter(F.col("name").like("%li%"))
        self.assertEqual(result.count(), 2)


class TestColumnNull(unittest.TestCase):
    """Tests for Column null handling."""
    
    @classmethod
    def setUpClass(cls):
        SparkSession._active_session = None
        SparkContext._active_context = None
        cls.spark = SparkSession.builder \
            .config("spark.mock.ui.console", "false") \
            .getOrCreate()
        
        cls.df = cls.spark.createDataFrame([
            (1, "Alice"),
            (2, None),
            (3, "Charlie"),
        ], ["id", "name"])
    
    @classmethod
    def tearDownClass(cls):
        cls.spark.stop()
    
    def test_is_null(self):
        """Test isNull method."""
        result = self.df.filter(F.col("name").isNull())
        self.assertEqual(result.count(), 1)
    
    def test_is_not_null(self):
        """Test isNotNull method."""
        result = self.df.filter(F.col("name").isNotNull())
        self.assertEqual(result.count(), 2)


class TestColumnAlias(unittest.TestCase):
    """Tests for Column alias functionality."""
    
    @classmethod
    def setUpClass(cls):
        SparkSession._active_session = None
        SparkContext._active_context = None
        cls.spark = SparkSession.builder \
            .config("spark.mock.ui.console", "false") \
            .getOrCreate()
        
        cls.df = cls.spark.createDataFrame([(1, "Alice")], ["id", "name"])
    
    @classmethod
    def tearDownClass(cls):
        cls.spark.stop()
    
    def test_alias(self):
        """Test alias method."""
        result = self.df.select(F.col("name").alias("employee_name"))
        self.assertEqual(result.columns, ["employee_name"])
    
    def test_name(self):
        """Test name method (alias for alias)."""
        col = F.col("id").name("new_id")
        self.assertIsInstance(col, Column)


class TestColumnCast(unittest.TestCase):
    """Tests for Column cast functionality."""
    
    @classmethod
    def setUpClass(cls):
        SparkSession._active_session = None
        SparkContext._active_context = None
        cls.spark = SparkSession.builder \
            .config("spark.mock.ui.console", "false") \
            .getOrCreate()
        
        cls.df = cls.spark.createDataFrame([(1, "42")], ["id", "value"])
    
    @classmethod
    def tearDownClass(cls):
        cls.spark.stop()
    
    def test_cast_to_int(self):
        """Test casting to integer."""
        result = self.df.withColumn("int_value", F.col("value").cast("int"))
        rows = result.collect()
        self.assertEqual(rows[0]["int_value"], 42)
    
    def test_cast_to_string(self):
        """Test casting to string."""
        result = self.df.withColumn("str_id", F.col("id").cast("string"))
        rows = result.collect()
        self.assertEqual(rows[0]["str_id"], "1")


if __name__ == "__main__":
    unittest.main()
