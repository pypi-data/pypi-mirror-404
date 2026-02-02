"""
Unit tests for SparkSession and related classes.
"""
import unittest
import tempfile
import os

from spark_mock.sql import SparkSession
from spark_mock.sql.session import SparkConf, SparkContext, SparkSessionBuilder


class TestSparkConf(unittest.TestCase):
    """Tests for SparkConf class."""
    
    def test_set_and_get(self):
        """Test setting and getting config values."""
        conf = SparkConf()
        conf.set("spark.app.name", "TestApp")
        self.assertEqual(conf.get("spark.app.name"), "TestApp")
    
    def test_get_default(self):
        """Test getting with default value."""
        conf = SparkConf()
        self.assertEqual(conf.get("nonexistent", "default"), "default")
        self.assertIsNone(conf.get("nonexistent"))
    
    def test_set_all(self):
        """Test setting multiple values."""
        conf = SparkConf()
        conf.setAll([("key1", "val1"), ("key2", "val2")])
        self.assertEqual(conf.get("key1"), "val1")
        self.assertEqual(conf.get("key2"), "val2")
    
    def test_get_all(self):
        """Test getting all config values."""
        conf = SparkConf()
        conf.set("k1", "v1")
        conf.set("k2", "v2")
        all_conf = conf.getAll()
        self.assertIn(("k1", "v1"), all_conf)
        self.assertIn(("k2", "v2"), all_conf)
    
    def test_set_app_name(self):
        """Test setAppName helper."""
        conf = SparkConf()
        result = conf.setAppName("MyApp")
        self.assertEqual(conf.get("spark.app.name"), "MyApp")
        self.assertIs(result, conf)  # Should return self for chaining
    
    def test_set_master(self):
        """Test setMaster helper."""
        conf = SparkConf()
        result = conf.setMaster("local[4]")
        self.assertEqual(conf.get("spark.master"), "local[4]")
        self.assertIs(result, conf)


class TestSparkContext(unittest.TestCase):
    """Tests for SparkContext class."""
    
    def setUp(self):
        SparkContext._active_context = None
    
    def tearDown(self):
        if SparkContext._active_context:
            SparkContext._active_context.stop()
    
    def test_get_or_create_new(self):
        """Test creating new context."""
        sc = SparkContext.getOrCreate()
        self.assertIsNotNone(sc)
        self.assertEqual(SparkContext._active_context, sc)
    
    def test_get_or_create_existing(self):
        """Test getting existing context."""
        sc1 = SparkContext.getOrCreate()
        sc2 = SparkContext.getOrCreate()
        self.assertIs(sc1, sc2)
    
    def test_default_parallelism(self):
        """Test default parallelism."""
        sc = SparkContext()
        self.assertEqual(sc.defaultParallelism, 4)
    
    def test_custom_parallelism(self):
        """Test custom parallelism via config."""
        conf = SparkConf()
        conf.set("spark.default.parallelism", 8)
        sc = SparkContext(conf)
        self.assertEqual(sc.defaultParallelism, 8)
    
    def test_application_id(self):
        """Test application ID."""
        sc = SparkContext()
        self.assertEqual(sc.applicationId, "local-spark-mock")
    
    def test_app_name(self):
        """Test app name."""
        conf = SparkConf()
        conf.setAppName("TestApp")
        sc = SparkContext(conf)
        self.assertEqual(sc.appName, "TestApp")
    
    def test_stop(self):
        """Test stopping context."""
        sc = SparkContext()
        sc.stop()
        self.assertTrue(sc._stopped)
        self.assertIsNone(SparkContext._active_context)


class TestSparkSessionBuilder(unittest.TestCase):
    """Tests for SparkSessionBuilder class."""
    
    def setUp(self):
        SparkSession._active_session = None
        SparkContext._active_context = None
    
    def tearDown(self):
        if SparkSession._active_session:
            SparkSession._active_session.stop()
    
    def test_app_name(self):
        """Test setting app name."""
        builder = SparkSessionBuilder()
        result = builder.appName("TestApp")
        self.assertIs(result, builder)  # Returns self
        self.assertEqual(builder._conf.get("spark.app.name"), "TestApp")
    
    def test_master(self):
        """Test setting master."""
        builder = SparkSessionBuilder()
        result = builder.master("local[*]")
        self.assertIs(result, builder)
        self.assertEqual(builder._conf.get("spark.master"), "local[*]")
    
    def test_config_key_value(self):
        """Test config with key-value pair."""
        builder = SparkSessionBuilder()
        result = builder.config("custom.key", "custom.value")
        self.assertIs(result, builder)
        self.assertEqual(builder._conf.get("custom.key"), "custom.value")
    
    def test_config_spark_conf(self):
        """Test config with SparkConf object."""
        conf = SparkConf()
        conf.set("from.conf", "value")
        
        builder = SparkSessionBuilder()
        builder.config(conf=conf)
        self.assertEqual(builder._conf.get("from.conf"), "value")
    
    def test_enable_hive_support(self):
        """Test enabling Hive support."""
        builder = SparkSessionBuilder()
        result = builder.enableHiveSupport()
        self.assertIs(result, builder)
        self.assertEqual(builder._conf.get("spark.sql.catalogImplementation"), "hive")
    
    def test_get_or_create(self):
        """Test getOrCreate creates session."""
        spark = SparkSessionBuilder().appName("Test").getOrCreate()
        self.assertIsNotNone(spark)
        self.assertEqual(SparkSession._active_session, spark)
    
    def test_get_or_create_returns_existing(self):
        """Test getOrCreate returns existing session."""
        spark1 = SparkSessionBuilder().appName("Test1").getOrCreate()
        spark2 = SparkSessionBuilder().appName("Test2").getOrCreate()
        self.assertIs(spark1, spark2)


class TestSparkSession(unittest.TestCase):
    """Tests for SparkSession class."""
    
    def setUp(self):
        SparkSession._active_session = None
        SparkContext._active_context = None
    
    def tearDown(self):
        if SparkSession._active_session:
            SparkSession._active_session.stop()
    
    def test_builder_access(self):
        """Test accessing builder class attribute."""
        builder = SparkSession.builder.appName("Test")
        self.assertIsInstance(builder, SparkSessionBuilder)
    
    def test_create_session(self):
        """Test creating SparkSession."""
        spark = SparkSession.builder.appName("TestApp").getOrCreate()
        self.assertIsNotNone(spark)
        self.assertEqual(str(spark), "SparkSession(appName=TestApp, partitions=4)")
    
    def test_get_active_session(self):
        """Test getting active session."""
        self.assertIsNone(SparkSession.getActiveSession())
        spark = SparkSession.builder.getOrCreate()
        self.assertEqual(SparkSession.getActiveSession(), spark)
    
    def test_spark_context(self):
        """Test getting SparkContext."""
        spark = SparkSession.builder.getOrCreate()
        self.assertIsNotNone(spark.sparkContext)
        self.assertIsInstance(spark.sparkContext, SparkContext)
    
    def test_catalog(self):
        """Test getting catalog."""
        spark = SparkSession.builder.getOrCreate()
        self.assertIsNotNone(spark.catalog)
    
    def test_version(self):
        """Test version property."""
        spark = SparkSession.builder.getOrCreate()
        self.assertEqual(spark.version, "spark-mock-0.1.0")
    
    def test_create_dataframe_from_tuples(self):
        """Test creating DataFrame from tuples."""
        spark = SparkSession.builder.getOrCreate()
        df = spark.createDataFrame([(1, "a"), (2, "b")], ["id", "name"])
        self.assertEqual(df.columns, ["id", "name"])
        self.assertEqual(df.count(), 2)
    
    def test_create_dataframe_from_dicts(self):
        """Test creating DataFrame from dicts."""
        spark = SparkSession.builder.getOrCreate()
        df = spark.createDataFrame([{"id": 1, "name": "a"}, {"id": 2, "name": "b"}])
        self.assertIn("id", df.columns)
        self.assertIn("name", df.columns)
        self.assertEqual(df.count(), 2)
    
    def test_range(self):
        """Test range method."""
        spark = SparkSession.builder.getOrCreate()
        df = spark.range(10)
        self.assertEqual(df.columns, ["id"])
        self.assertEqual(df.count(), 10)
    
    def test_range_with_start_end(self):
        """Test range with start and end."""
        spark = SparkSession.builder.getOrCreate()
        df = spark.range(5, 10)
        self.assertEqual(df.count(), 5)
        rows = df.collect()
        self.assertEqual(rows[0].id, 5)
    
    def test_range_with_step(self):
        """Test range with step."""
        spark = SparkSession.builder.getOrCreate()
        df = spark.range(0, 10, 2)
        self.assertEqual(df.count(), 5)
    
    def test_context_manager(self):
        """Test SparkSession as context manager."""
        with SparkSession.builder.appName("ContextTest").getOrCreate() as spark:
            self.assertIsNotNone(spark)
        self.assertIsNone(SparkSession._active_session)
    
    def test_stop(self):
        """Test stopping session."""
        spark = SparkSession.builder.getOrCreate()
        spark.stop()
        self.assertIsNone(SparkSession._active_session)
    
    def test_new_session(self):
        """Test creating new session."""
        spark1 = SparkSession.builder.appName("Test1").getOrCreate()
        spark2 = spark1.newSession()
        self.assertIsNot(spark1, spark2)


class TestSparkSessionConfig(unittest.TestCase):
    """Tests for SparkSession configuration."""
    
    def setUp(self):
        SparkSession._active_session = None
        SparkContext._active_context = None
    
    def tearDown(self):
        if SparkSession._active_session:
            SparkSession._active_session.stop()
    
    def test_custom_partitions(self):
        """Test custom partition count."""
        spark = SparkSession.builder \
            .config("spark.mock.partitions", 8) \
            .getOrCreate()
        self.assertEqual(spark._num_partitions, 8)
    
    def test_disable_console_ui(self):
        """Test disabling console UI."""
        spark = SparkSession.builder \
            .config("spark.mock.ui.console", "false") \
            .getOrCreate()
        self.assertFalse(spark._console_ui_enabled)
    
    def test_enable_html_ui(self):
        """Test enabling HTML UI."""
        spark = SparkSession.builder \
            .config("spark.mock.ui.html", "true") \
            .getOrCreate()
        self.assertTrue(spark._html_ui_enabled)
        self.assertIsNotNone(spark._html_ui)


if __name__ == "__main__":
    unittest.main()
