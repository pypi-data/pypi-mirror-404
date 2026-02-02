"""
Unit tests for DataFrame class.
"""
import unittest
import polars as pl

from spark_mock.sql import SparkSession
from spark_mock.sql import functions as F
from spark_mock.sql.session import SparkContext


class TestDataFrameCreation(unittest.TestCase):
    """Tests for DataFrame creation."""
    
    @classmethod
    def setUpClass(cls):
        SparkSession._active_session = None
        SparkContext._active_context = None
        cls.spark = SparkSession.builder \
            .appName("TestDataFrame") \
            .config("spark.mock.ui.console", "false") \
            .getOrCreate()
    
    @classmethod
    def tearDownClass(cls):
        cls.spark.stop()
    
    def test_create_from_tuples(self):
        """Test creating DataFrame from tuples."""
        df = self.spark.createDataFrame(
            [(1, "a"), (2, "b"), (3, "c")],
            ["id", "name"]
        )
        self.assertEqual(df.columns, ["id", "name"])
        self.assertEqual(df.count(), 3)
    
    def test_create_from_dicts(self):
        """Test creating DataFrame from dicts."""
        df = self.spark.createDataFrame([
            {"id": 1, "name": "a"},
            {"id": 2, "name": "b"}
        ])
        self.assertEqual(df.count(), 2)
    
    def test_columns_property(self):
        """Test columns property."""
        df = self.spark.createDataFrame([(1, 2, 3)], ["a", "b", "c"])
        self.assertEqual(df.columns, ["a", "b", "c"])
    
    def test_schema_property(self):
        """Test schema property."""
        df = self.spark.createDataFrame([(1, "text")], ["id", "name"])
        schema = df.schema
        self.assertEqual(len(schema.fields), 2)


class TestDataFrameTransformations(unittest.TestCase):
    """Tests for DataFrame transformations."""
    
    @classmethod
    def setUpClass(cls):
        SparkSession._active_session = None
        SparkContext._active_context = None
        cls.spark = SparkSession.builder \
            .appName("TestTransformations") \
            .config("spark.mock.ui.console", "false") \
            .getOrCreate()
        
        cls.df = cls.spark.createDataFrame([
            (1, "Alice", 30, 50000),
            (2, "Bob", 25, 45000),
            (3, "Charlie", 35, 60000),
            (4, "Diana", 28, 52000),
        ], ["id", "name", "age", "salary"])
    
    @classmethod
    def tearDownClass(cls):
        cls.spark.stop()
    
    def test_select_single_column(self):
        """Test selecting single column."""
        result = self.df.select("name")
        self.assertEqual(result.columns, ["name"])
        self.assertEqual(result.count(), 4)
    
    def test_select_multiple_columns(self):
        """Test selecting multiple columns."""
        result = self.df.select("name", "age")
        self.assertEqual(result.columns, ["name", "age"])
    
    def test_select_with_column_object(self):
        """Test selecting with Column object."""
        result = self.df.select(F.col("name"), F.col("age"))
        self.assertEqual(result.columns, ["name", "age"])
    
    def test_select_with_alias(self):
        """Test selecting with alias."""
        result = self.df.select(F.col("name").alias("employee_name"))
        self.assertEqual(result.columns, ["employee_name"])
    
    def test_filter_greater_than(self):
        """Test filter with greater than."""
        result = self.df.filter(F.col("age") > 28)
        self.assertEqual(result.count(), 2)  # Alice (30), Charlie (35)
    
    def test_filter_less_than(self):
        """Test filter with less than."""
        result = self.df.filter(F.col("age") < 30)
        self.assertEqual(result.count(), 2)  # Bob (25), Diana (28)
    
    def test_filter_equals(self):
        """Test filter with equals."""
        result = self.df.filter(F.col("name") == "Alice")
        self.assertEqual(result.count(), 1)
    
    def test_filter_with_column_expression(self):
        """Test filter with column expression."""
        result = self.df.filter(F.col("age") > 28)
        self.assertEqual(result.count(), 2)
    
    def test_where_alias(self):
        """Test where (alias for filter)."""
        result = self.df.where(F.col("age") > 28)
        self.assertEqual(result.count(), 2)
    
    def test_with_column(self):
        """Test withColumn."""
        result = self.df.withColumn("bonus", F.col("salary") * 0.1)
        self.assertIn("bonus", result.columns)
        self.assertEqual(len(result.columns), 5)
    
    def test_with_column_renamed(self):
        """Test withColumnRenamed."""
        result = self.df.withColumnRenamed("name", "employee_name")
        self.assertIn("employee_name", result.columns)
        self.assertNotIn("name", result.columns)
    
    def test_drop_single_column(self):
        """Test dropping single column."""
        result = self.df.drop("salary")
        self.assertNotIn("salary", result.columns)
        self.assertEqual(len(result.columns), 3)
    
    def test_drop_multiple_columns(self):
        """Test dropping multiple columns."""
        result = self.df.drop("salary", "age")
        self.assertNotIn("salary", result.columns)
        self.assertNotIn("age", result.columns)
    
    def test_limit(self):
        """Test limit."""
        result = self.df.limit(2)
        self.assertEqual(result.count(), 2)
    
    def test_distinct(self):
        """Test distinct."""
        df = self.spark.createDataFrame([
            (1, "a"), (1, "a"), (2, "b")
        ], ["id", "name"])
        result = df.distinct()
        self.assertEqual(result.count(), 2)
    
    def test_dropDuplicates(self):
        """Test dropDuplicates."""
        df = self.spark.createDataFrame([
            (1, "a"), (1, "b"), (2, "a")
        ], ["id", "name"])
        result = df.dropDuplicates(["id"])
        self.assertEqual(result.count(), 2)


class TestDataFrameGroupBy(unittest.TestCase):
    """Tests for DataFrame groupBy operations."""
    
    @classmethod
    def setUpClass(cls):
        SparkSession._active_session = None
        SparkContext._active_context = None
        cls.spark = SparkSession.builder \
            .appName("TestGroupBy") \
            .config("spark.mock.ui.console", "false") \
            .getOrCreate()
        
        cls.df = cls.spark.createDataFrame([
            ("Engineering", "Alice", 75000),
            ("Engineering", "Bob", 80000),
            ("Marketing", "Charlie", 60000),
            ("Marketing", "Diana", 65000),
            ("Sales", "Eve", 55000),
        ], ["dept", "name", "salary"])
    
    @classmethod
    def tearDownClass(cls):
        cls.spark.stop()
    
    def test_count(self):
        """Test groupBy count."""
        result = self.df.groupBy("dept").count()
        self.assertIn("count", result.columns)
        self.assertEqual(result.count(), 3)  # 3 departments
    
    def test_sum(self):
        """Test groupBy sum."""
        result = self.df.groupBy("dept").sum("salary")
        self.assertIn("sum(salary)", result.columns)
    
    def test_avg(self):
        """Test groupBy avg."""
        result = self.df.groupBy("dept").avg("salary")
        self.assertIn("avg(salary)", result.columns)
    
    def test_min(self):
        """Test groupBy min."""
        result = self.df.groupBy("dept").min("salary")
        self.assertIn("min(salary)", result.columns)
    
    def test_max(self):
        """Test groupBy max."""
        result = self.df.groupBy("dept").max("salary")
        self.assertIn("max(salary)", result.columns)
    
    def test_agg_with_functions(self):
        """Test groupBy agg with functions."""
        result = self.df.groupBy("dept").agg(
            F.count("*").alias("count"),
            F.avg("salary").alias("avg_salary")
        )
        self.assertIn("count", result.columns)
        self.assertIn("avg_salary", result.columns)


class TestDataFrameJoin(unittest.TestCase):
    """Tests for DataFrame join operations."""
    
    @classmethod
    def setUpClass(cls):
        SparkSession._active_session = None
        SparkContext._active_context = None
        cls.spark = SparkSession.builder \
            .appName("TestJoin") \
            .config("spark.mock.ui.console", "false") \
            .getOrCreate()
        
        cls.employees = cls.spark.createDataFrame([
            (1, "Alice", "E1"),
            (2, "Bob", "E2"),
            (3, "Charlie", "E3"),
        ], ["id", "name", "dept_id"])
        
        cls.departments = cls.spark.createDataFrame([
            ("E1", "Engineering"),
            ("E2", "Marketing"),
            ("E4", "Sales"),
        ], ["dept_id", "dept_name"])
    
    @classmethod
    def tearDownClass(cls):
        cls.spark.stop()
    
    def test_inner_join(self):
        """Test inner join."""
        result = self.employees.join(self.departments, on="dept_id", how="inner")
        self.assertEqual(result.count(), 2)  # Alice, Bob
    
    def test_left_join(self):
        """Test left join."""
        result = self.employees.join(self.departments, on="dept_id", how="left")
        self.assertEqual(result.count(), 3)  # All employees
    
    def test_right_join(self):
        """Test right join."""
        result = self.employees.join(self.departments, on="dept_id", how="right")
        self.assertEqual(result.count(), 3)  # E1, E2, E4


class TestDataFrameActions(unittest.TestCase):
    """Tests for DataFrame actions."""
    
    @classmethod
    def setUpClass(cls):
        SparkSession._active_session = None
        SparkContext._active_context = None
        cls.spark = SparkSession.builder \
            .appName("TestActions") \
            .config("spark.mock.ui.console", "false") \
            .getOrCreate()
        
        cls.df = cls.spark.createDataFrame([
            (1, "Alice", 30),
            (2, "Bob", 25),
            (3, "Charlie", 35),
        ], ["id", "name", "age"])
    
    @classmethod
    def tearDownClass(cls):
        cls.spark.stop()
    
    def test_count(self):
        """Test count action."""
        self.assertEqual(self.df.count(), 3)
    
    def test_collect(self):
        """Test collect action."""
        rows = self.df.collect()
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0].name, "Alice")
    
    def test_first(self):
        """Test first action."""
        row = self.df.first()
        self.assertEqual(row.id, 1)
    
    def test_head(self):
        """Test head action."""
        row = self.df.head()
        self.assertEqual(row.id, 1)
    
    def test_head_n(self):
        """Test head(n) action."""
        rows = self.df.head(2)
        self.assertEqual(len(rows), 2)
    
    def test_take(self):
        """Test take action."""
        rows = self.df.take(2)
        self.assertEqual(len(rows), 2)
    
    def test_to_pandas(self):
        """Test toPandas action."""
        pdf = self.df.toPandas()
        self.assertEqual(len(pdf), 3)
        self.assertIn("name", pdf.columns)
    
    def test_to_polars(self):
        """Test toPolars action."""
        pldf = self.df.toPolars()
        self.assertIsInstance(pldf, pl.DataFrame)
        self.assertEqual(len(pldf), 3)


class TestDataFrameUnion(unittest.TestCase):
    """Tests for DataFrame union operations."""
    
    @classmethod
    def setUpClass(cls):
        SparkSession._active_session = None
        SparkContext._active_context = None
        cls.spark = SparkSession.builder \
            .appName("TestUnion") \
            .config("spark.mock.ui.console", "false") \
            .getOrCreate()
    
    @classmethod
    def tearDownClass(cls):
        cls.spark.stop()
    
    def test_union(self):
        """Test union."""
        df1 = self.spark.createDataFrame([(1,), (2,)], ["id"])
        df2 = self.spark.createDataFrame([(3,), (4,)], ["id"])
        result = df1.union(df2)
        self.assertEqual(result.count(), 4)
    
    def test_union_all(self):
        """Test unionAll."""
        df1 = self.spark.createDataFrame([(1,), (2,)], ["id"])
        df2 = self.spark.createDataFrame([(2,), (3,)], ["id"])
        result = df1.unionAll(df2)
        self.assertEqual(result.count(), 4)  # Includes duplicates


if __name__ == "__main__":
    unittest.main()
