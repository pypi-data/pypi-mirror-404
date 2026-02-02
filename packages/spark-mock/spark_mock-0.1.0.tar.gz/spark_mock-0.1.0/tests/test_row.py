"""
Unit tests for Row class.
"""
import unittest

from spark_mock.sql import SparkSession
from spark_mock.sql.row import Row
from spark_mock.sql.session import SparkContext


class TestRowCreation(unittest.TestCase):
    """Tests for Row creation."""
    
    def test_row_from_args(self):
        """Test creating Row from positional arguments."""
        row = Row(1, "Alice", 30)
        self.assertEqual(len(row), 3)
    
    def test_row_from_kwargs(self):
        """Test creating Row from keyword arguments."""
        row = Row(id=1, name="Alice", age=30)
        self.assertEqual(row.id, 1)
        self.assertEqual(row.name, "Alice")
        self.assertEqual(row.age, 30)
    
    def test_row_factory(self):
        """Test Row factory pattern."""
        PersonRow = Row("id", "name", "age")
        person = PersonRow(1, "Alice", 30)
        self.assertEqual(person.id, 1)


class TestRowAccess(unittest.TestCase):
    """Tests for Row access patterns."""
    
    def setUp(self):
        self.row = Row(id=1, name="Alice", age=30)
    
    def test_attribute_access(self):
        """Test accessing Row values by attribute."""
        self.assertEqual(self.row.name, "Alice")
    
    def test_index_access(self):
        """Test accessing Row values by index."""
        self.assertEqual(self.row[0], 1)
        self.assertEqual(self.row[1], "Alice")
    
    def test_negative_index(self):
        """Test negative index access."""
        self.assertEqual(self.row[-1], 30)
    
    def test_dict_access(self):
        """Test accessing Row values by key."""
        self.assertEqual(self.row["name"], "Alice")
    
    def test_as_dict(self):
        """Test converting Row to dict."""
        d = self.row.asDict()
        self.assertEqual(d["id"], 1)
        self.assertEqual(d["name"], "Alice")
    
    def test_len(self):
        """Test Row length."""
        self.assertEqual(len(self.row), 3)
    
    def test_contains(self):
        """Test 'in' operator."""
        self.assertIn("name", self.row)
        self.assertNotIn("salary", self.row)
    
    def test_iteration(self):
        """Test iterating over Row values."""
        values = list(self.row)
        self.assertEqual(values, [1, "Alice", 30])


class TestRowComparison(unittest.TestCase):
    """Tests for Row comparison."""
    
    def test_equal_rows(self):
        """Test equal Rows."""
        row1 = Row(id=1, name="Alice")
        row2 = Row(id=1, name="Alice")
        self.assertEqual(row1, row2)
    
    def test_unequal_rows(self):
        """Test unequal Rows."""
        row1 = Row(id=1, name="Alice")
        row2 = Row(id=2, name="Bob")
        self.assertNotEqual(row1, row2)


class TestRowFromDataFrame(unittest.TestCase):
    """Tests for Row from DataFrame operations."""
    
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
    
    def test_collect_returns_rows(self):
        """Test that collect returns Row objects."""
        df = self.spark.createDataFrame([(1, "Alice")], ["id", "name"])
        rows = df.collect()
        self.assertIsInstance(rows[0], Row)
    
    def test_row_attribute_access_from_df(self):
        """Test Row attribute access from DataFrame."""
        df = self.spark.createDataFrame([(1, "Alice", 30)], ["id", "name", "age"])
        row = df.first()
        self.assertEqual(row.name, "Alice")
        self.assertEqual(row.age, 30)
    
    def test_row_dict_access_from_df(self):
        """Test Row dict access from DataFrame."""
        df = self.spark.createDataFrame([(1, "Alice")], ["id", "name"])
        row = df.first()
        self.assertEqual(row["id"], 1)


if __name__ == "__main__":
    unittest.main()
