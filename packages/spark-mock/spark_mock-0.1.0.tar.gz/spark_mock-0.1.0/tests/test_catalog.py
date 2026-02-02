"""
Unit tests for Catalog class.
"""
import unittest

from spark_mock.sql import SparkSession
from spark_mock.sql.session import SparkContext


class TestCatalogTables(unittest.TestCase):
    """Tests for Catalog table operations."""
    
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
    
    def tearDown(self):
        # Clear all tables between tests
        for table in self.spark.catalog.listTables():
            try:
                self.spark.catalog.dropTempView(table.name)
            except:
                pass
    
    def test_list_tables_empty(self):
        """Test listing tables when empty."""
        tables = self.spark.catalog.listTables()
        self.assertEqual(len(tables), 0)
    
    def test_create_temp_view(self):
        """Test creating temporary view."""
        df = self.spark.createDataFrame([(1, "a")], ["id", "name"])
        df.createTempView("test_view")
        
        tables = self.spark.catalog.listTables()
        self.assertEqual(len(tables), 1)
        self.assertEqual(tables[0].name, "test_view")
    
    def test_create_or_replace_temp_view(self):
        """Test createOrReplaceTempView."""
        df1 = self.spark.createDataFrame([(1, "a")], ["id", "name"])
        df1.createTempView("my_view")
        
        df2 = self.spark.createDataFrame([(2, "b")], ["id", "name"])
        df2.createOrReplaceTempView("my_view")
        
        tables = self.spark.catalog.listTables()
        self.assertEqual(len(tables), 1)
    
    def test_drop_temp_view(self):
        """Test dropping temp view."""
        df = self.spark.createDataFrame([(1, "a")], ["id", "name"])
        df.createTempView("to_drop")
        
        result = self.spark.catalog.dropTempView("to_drop")
        self.assertTrue(result)
        
        tables = self.spark.catalog.listTables()
        self.assertEqual(len(tables), 0)
    
    def test_drop_nonexistent_view(self):
        """Test dropping non-existent view."""
        result = self.spark.catalog.dropTempView("nonexistent")
        self.assertFalse(result)
    
    def test_table_exists(self):
        """Test checking if table exists."""
        df = self.spark.createDataFrame([(1,)], ["id"])
        df.createTempView("exists_view")
        
        self.assertTrue(self.spark.catalog.tableExists("exists_view"))
        self.assertFalse(self.spark.catalog.tableExists("not_exists"))
    
    def test_get_table(self):
        """Test getting table as DataFrame."""
        df = self.spark.createDataFrame([(1, "test")], ["id", "name"])
        df.createTempView("get_view")
        
        result = self.spark.table("get_view")
        self.assertEqual(result.count(), 1)
        self.assertEqual(result.columns, ["id", "name"])


class TestCatalogDatabases(unittest.TestCase):
    """Tests for Catalog database operations."""
    
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
    
    def test_list_databases(self):
        """Test listing databases."""
        databases = self.spark.catalog.listDatabases()
        self.assertGreaterEqual(len(databases), 1)  # At least default db
    
    def test_current_database(self):
        """Test getting current database."""
        current = self.spark.catalog.currentDatabase()
        self.assertEqual(current, "default")
    
    def test_set_current_database(self):
        """Test setting current database."""
        self.spark.catalog.setCurrentDatabase("test_db")
        self.assertEqual(self.spark.catalog.currentDatabase(), "test_db")
        # Reset
        self.spark.catalog.setCurrentDatabase("default")


class TestCatalogColumns(unittest.TestCase):
    """Tests for Catalog column operations."""
    
    @classmethod
    def setUpClass(cls):
        SparkSession._active_session = None
        SparkContext._active_context = None
        cls.spark = SparkSession.builder \
            .config("spark.mock.ui.console", "false") \
            .getOrCreate()
        
        # Create a view for column tests
        cls.df = cls.spark.createDataFrame([
            (1, "Alice", 30),
            (2, "Bob", 25)
        ], ["id", "name", "age"])
        cls.df.createTempView("employees")
    
    @classmethod
    def tearDownClass(cls):
        cls.spark.catalog.dropTempView("employees")
        cls.spark.stop()
    
    def test_list_columns(self):
        """Test listing columns."""
        columns = self.spark.catalog.listColumns("employees")
        self.assertEqual(len(columns), 3)
        
        names = [c.name for c in columns]
        self.assertIn("id", names)
        self.assertIn("name", names)
        self.assertIn("age", names)


if __name__ == "__main__":
    unittest.main()
