"""
Unit tests for Window functions.
"""
import unittest

from spark_mock.sql import SparkSession
from spark_mock.sql import functions as F
from spark_mock.sql.window import Window, WindowSpec
from spark_mock.sql.session import SparkContext


class TestWindowSpec(unittest.TestCase):
    """Tests for WindowSpec class."""
    
    def test_window_partition_by(self):
        """Test Window partitionBy."""
        spec = Window.partitionBy("dept")
        self.assertIsInstance(spec, WindowSpec)
    
    def test_window_order_by(self):
        """Test Window orderBy."""
        spec = Window.orderBy("salary")
        self.assertIsInstance(spec, WindowSpec)
    
    def test_window_partition_and_order(self):
        """Test Window partitionBy and orderBy."""
        spec = Window.partitionBy("dept").orderBy("salary")
        self.assertIsInstance(spec, WindowSpec)
    
    def test_window_rows_between(self):
        """Test Window rowsBetween."""
        spec = Window.partitionBy("dept").orderBy("date")
        spec = spec.rowsBetween(-1, 1)
        self.assertIsInstance(spec, WindowSpec)


class TestWindowFunctions(unittest.TestCase):
    """Tests for window functions with DataFrame."""
    
    @classmethod
    def setUpClass(cls):
        SparkSession._active_session = None
        SparkContext._active_context = None
        cls.spark = SparkSession.builder \
            .config("spark.mock.ui.console", "false") \
            .getOrCreate()
        
        cls.df = cls.spark.createDataFrame([
            ("Engineering", "Alice", 75000, 1),
            ("Engineering", "Bob", 80000, 2),
            ("Engineering", "Charlie", 85000, 3),
            ("Marketing", "Diana", 60000, 1),
            ("Marketing", "Eve", 65000, 2),
        ], ["dept", "name", "salary", "hire_order"])
    
    @classmethod
    def tearDownClass(cls):
        cls.spark.stop()
    
    def test_row_number(self):
        """Test row_number window function."""
        window = Window.partitionBy("dept").orderBy("salary")
        result = self.df.withColumn("row_num", F.row_number().over(window))
        
        self.assertIn("row_num", result.columns)
        rows = result.collect()
        self.assertEqual(len(rows), 5)
    
    def test_rank(self):
        """Test rank window function."""
        window = Window.partitionBy("dept").orderBy("salary")
        result = self.df.withColumn("rank", F.rank().over(window))
        
        self.assertIn("rank", result.columns)
    
    def test_dense_rank(self):
        """Test dense_rank window function."""
        window = Window.partitionBy("dept").orderBy("salary")
        result = self.df.withColumn("dense_rank", F.dense_rank().over(window))
        
        self.assertIn("dense_rank", result.columns)
    
    def test_lag(self):
        """Test lag window function."""
        window = Window.partitionBy("dept").orderBy("hire_order")
        result = self.df.withColumn("prev_salary", F.lag("salary", 1).over(window))
        
        self.assertIn("prev_salary", result.columns)
    
    def test_lead(self):
        """Test lead window function."""
        window = Window.partitionBy("dept").orderBy("hire_order")
        result = self.df.withColumn("next_salary", F.lead("salary", 1).over(window))
        
        self.assertIn("next_salary", result.columns)


if __name__ == "__main__":
    unittest.main()
