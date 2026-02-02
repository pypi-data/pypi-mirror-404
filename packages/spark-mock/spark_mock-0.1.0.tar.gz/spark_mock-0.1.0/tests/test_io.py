"""
Unit tests for I/O operations.
"""
import unittest
import tempfile
import os
import shutil

from spark_mock.sql import SparkSession
from spark_mock.sql.session import SparkContext


class TestDataFrameReaderCSV(unittest.TestCase):
    """Tests for reading CSV files."""
    
    @classmethod
    def setUpClass(cls):
        SparkSession._active_session = None
        SparkContext._active_context = None
        cls.spark = SparkSession.builder \
            .config("spark.mock.ui.console", "false") \
            .getOrCreate()
        
        # Create temp directory
        cls.temp_dir = tempfile.mkdtemp()
        
        # Create CSV file
        cls.csv_path = os.path.join(cls.temp_dir, "test.csv")
        with open(cls.csv_path, "w") as f:
            f.write("id,name,age\n")
            f.write("1,Alice,30\n")
            f.write("2,Bob,25\n")
            f.write("3,Charlie,35\n")
    
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.temp_dir)
        cls.spark.stop()
    
    def test_read_csv_with_header(self):
        """Test reading CSV with header."""
        df = self.spark.read.csv(self.csv_path, header=True)
        self.assertEqual(df.count(), 3)
        self.assertIn("name", df.columns)
    
    def test_read_csv_infer_schema(self):
        """Test reading CSV with schema inference."""
        df = self.spark.read.csv(self.csv_path, header=True, inferSchema=True)
        self.assertEqual(df.count(), 3)


class TestDataFrameReaderJSON(unittest.TestCase):
    """Tests for reading JSON files."""
    
    @classmethod
    def setUpClass(cls):
        SparkSession._active_session = None
        SparkContext._active_context = None
        cls.spark = SparkSession.builder \
            .config("spark.mock.ui.console", "false") \
            .getOrCreate()
        
        cls.temp_dir = tempfile.mkdtemp()
        
        # Create JSON file (newline-delimited)
        cls.json_path = os.path.join(cls.temp_dir, "test.json")
        with open(cls.json_path, "w") as f:
            f.write('{"id": 1, "name": "Alice"}\n')
            f.write('{"id": 2, "name": "Bob"}\n')
    
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.temp_dir)
        cls.spark.stop()
    
    def test_read_json(self):
        """Test reading JSON file."""
        df = self.spark.read.json(self.json_path)
        self.assertEqual(df.count(), 2)
        self.assertIn("name", df.columns)


class TestDataFrameReaderParquet(unittest.TestCase):
    """Tests for reading Parquet files."""
    
    @classmethod  
    def setUpClass(cls):
        SparkSession._active_session = None
        SparkContext._active_context = None
        cls.spark = SparkSession.builder \
            .config("spark.mock.ui.console", "false") \
            .getOrCreate()
        
        cls.temp_dir = tempfile.mkdtemp()
        
        # Create test DataFrame and save as Parquet
        cls.parquet_path = os.path.join(cls.temp_dir, "test.parquet")
        df = cls.spark.createDataFrame([
            (1, "Alice"),
            (2, "Bob")
        ], ["id", "name"])
        df.toPolars().write_parquet(cls.parquet_path)
    
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.temp_dir)
        cls.spark.stop()
    
    def test_read_parquet(self):
        """Test reading Parquet file."""
        df = self.spark.read.parquet(self.parquet_path)
        self.assertEqual(df.count(), 2)


class TestDataFrameWriterCSV(unittest.TestCase):
    """Tests for writing CSV files."""
    
    @classmethod
    def setUpClass(cls):
        SparkSession._active_session = None
        SparkContext._active_context = None
        cls.spark = SparkSession.builder \
            .config("spark.mock.ui.console", "false") \
            .getOrCreate()
        
        cls.temp_dir = tempfile.mkdtemp()
    
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.temp_dir)
        cls.spark.stop()
    
    def test_write_csv(self):
        """Test writing CSV file."""
        df = self.spark.createDataFrame([
            (1, "Alice"),
            (2, "Bob")
        ], ["id", "name"])
        
        output_path = os.path.join(self.temp_dir, "output_csv")
        df.write.csv(output_path)
        
        # Verify output exists
        self.assertTrue(os.path.exists(output_path))
    
    def test_write_csv_with_header(self):
        """Test writing CSV with header."""
        df = self.spark.createDataFrame([(1, "test")], ["id", "name"])
        output_path = os.path.join(self.temp_dir, "output_header")
        df.write.option("header", "true").csv(output_path)
        
        self.assertTrue(os.path.exists(output_path))


class TestDataFrameWriterJSON(unittest.TestCase):
    """Tests for writing JSON files."""
    
    @classmethod
    def setUpClass(cls):
        SparkSession._active_session = None
        SparkContext._active_context = None
        cls.spark = SparkSession.builder \
            .config("spark.mock.ui.console", "false") \
            .getOrCreate()
        
        cls.temp_dir = tempfile.mkdtemp()
    
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.temp_dir)
        cls.spark.stop()
    
    def test_write_json(self):
        """Test writing JSON file."""
        df = self.spark.createDataFrame([
            (1, "Alice"),
            (2, "Bob")
        ], ["id", "name"])
        
        output_path = os.path.join(self.temp_dir, "output_json")
        df.write.json(output_path)
        
        self.assertTrue(os.path.exists(output_path))


class TestDataFrameWriterParquet(unittest.TestCase):
    """Tests for writing Parquet files."""
    
    @classmethod
    def setUpClass(cls):
        SparkSession._active_session = None
        SparkContext._active_context = None
        cls.spark = SparkSession.builder \
            .config("spark.mock.ui.console", "false") \
            .getOrCreate()
        
        cls.temp_dir = tempfile.mkdtemp()
    
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.temp_dir)
        cls.spark.stop()
    
    def test_write_parquet(self):
        """Test writing Parquet file."""
        df = self.spark.createDataFrame([
            (1, "Alice"),
            (2, "Bob")
        ], ["id", "name"])
        
        output_path = os.path.join(self.temp_dir, "output.parquet")
        df.write.parquet(output_path)
        
        self.assertTrue(os.path.exists(output_path))
    
    def test_write_and_read_parquet(self):
        """Test writing and reading back Parquet."""
        df = self.spark.createDataFrame([
            (1, "Alice", 30),
            (2, "Bob", 25)
        ], ["id", "name", "age"])
        
        output_path = os.path.join(self.temp_dir, "roundtrip.parquet")
        df.write.parquet(output_path)
        
        df_read = self.spark.read.parquet(output_path)
        self.assertEqual(df_read.count(), 2)
        self.assertEqual(df_read.columns, ["id", "name", "age"])


class TestWriteModes(unittest.TestCase):
    """Tests for write modes."""
    
    @classmethod
    def setUpClass(cls):
        SparkSession._active_session = None
        SparkContext._active_context = None
        cls.spark = SparkSession.builder \
            .config("spark.mock.ui.console", "false") \
            .getOrCreate()
        
        cls.temp_dir = tempfile.mkdtemp()
    
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.temp_dir)
        cls.spark.stop()
    
    def test_mode_overwrite(self):
        """Test overwrite mode."""
        df = self.spark.createDataFrame([(1,)], ["id"])
        output_path = os.path.join(self.temp_dir, "overwrite.parquet")
        
        # Write first time
        df.write.parquet(output_path)
        
        # Write again with overwrite
        df2 = self.spark.createDataFrame([(2,), (3,)], ["id"])
        df2.write.mode("overwrite").parquet(output_path)
        
        # Read back
        df_read = self.spark.read.parquet(output_path)
        self.assertEqual(df_read.count(), 2)
    
    def test_mode_error_on_existing(self):
        """Test error mode on existing data."""
        df = self.spark.createDataFrame([(1,)], ["id"])
        output_path = os.path.join(self.temp_dir, "error_mode.parquet")
        
        df.write.parquet(output_path)
        
        # Should raise exception
        with self.assertRaises(Exception):
            df.write.mode("error").parquet(output_path)
    
    def test_mode_ignore(self):
        """Test ignore mode."""
        df = self.spark.createDataFrame([(1,)], ["id"])
        output_path = os.path.join(self.temp_dir, "ignore_mode.parquet")
        
        df.write.parquet(output_path)
        
        # Write with ignore - should not raise
        df2 = self.spark.createDataFrame([(999,)], ["id"])
        df2.write.mode("ignore").parquet(output_path)
        
        # Original data should remain
        df_read = self.spark.read.parquet(output_path)
        self.assertEqual(df_read.count(), 1)


if __name__ == "__main__":
    unittest.main()
