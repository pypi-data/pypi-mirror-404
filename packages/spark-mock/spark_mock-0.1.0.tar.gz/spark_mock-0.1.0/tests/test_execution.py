"""
Unit tests for execution engine and lazy evaluation.
"""
import unittest

from spark_mock.core.execution import ExecutionEngine, JobMetrics
from spark_mock.core.lazy import LazyExecutionPlan, OperationType, Operation
from spark_mock.core.partition import (
    PartitionManager, Partition, PartitionInfo, ShuffleStats
)


class TestPartition(unittest.TestCase):
    """Tests for Partition class."""
    
    def test_partition_creation(self):
        """Test creating a Partition."""
        p = Partition(id=0, num_rows=100, size_bytes=1024)
        self.assertEqual(p.id, 0)
        self.assertEqual(p.num_rows, 100)
        self.assertEqual(p.size_bytes, 1024)
    
    def test_partition_repr(self):
        """Test Partition string representation."""
        p = Partition(id=1, num_rows=50, size_bytes=512)
        self.assertIn("id=1", repr(p))
        self.assertIn("rows=50", repr(p))


class TestPartitionInfo(unittest.TestCase):
    """Tests for PartitionInfo class."""
    
    def test_partition_info(self):
        """Test PartitionInfo."""
        info = PartitionInfo(
            num_partitions=2,
            partitions=[
                Partition(id=0, num_rows=50, size_bytes=500),
                Partition(id=1, num_rows=50, size_bytes=500)
            ]
        )
        self.assertEqual(info.total_rows(), 100)
        self.assertEqual(info.total_size(), 1000)


class TestPartitionManager(unittest.TestCase):
    """Tests for PartitionManager class."""
    
    def test_default_partitions(self):
        """Test default partition count."""
        pm = PartitionManager()
        self.assertEqual(pm.default_partitions, 4)
    
    def test_custom_partitions(self):
        """Test custom partition count."""
        pm = PartitionManager(default_partitions=8)
        self.assertEqual(pm.default_partitions, 8)


class TestShuffleStats(unittest.TestCase):
    """Tests for ShuffleStats class."""
    
    def test_initial_stats(self):
        """Test initial shuffle stats."""
        stats = ShuffleStats()
        self.assertEqual(stats.shuffle_read_bytes, 0)
        self.assertEqual(stats.shuffle_write_bytes, 0)
    
    def test_add_shuffle(self):
        """Test adding shuffle stats."""
        stats = ShuffleStats()
        stats.add_shuffle(records=100, size_bytes=1024)
        
        self.assertEqual(stats.shuffle_read_bytes, 1024)
        self.assertEqual(stats.shuffle_write_bytes, 1024)
        self.assertEqual(stats.shuffle_read_records, 100)
    
    def test_accumulate_shuffles(self):
        """Test accumulating multiple shuffles."""
        stats = ShuffleStats()
        stats.add_shuffle(records=100, size_bytes=1000)
        stats.add_shuffle(records=200, size_bytes=2000)
        
        self.assertEqual(stats.shuffle_read_bytes, 3000)
        self.assertEqual(stats.shuffle_read_records, 300)


class TestOperationType(unittest.TestCase):
    """Tests for OperationType enum."""
    
    def test_operation_types_exist(self):
        """Test that operation types exist."""
        self.assertIsNotNone(OperationType.SELECT)
        self.assertIsNotNone(OperationType.FILTER)
        self.assertIsNotNone(OperationType.JOIN)
        self.assertIsNotNone(OperationType.GROUP_BY)


class TestOperation(unittest.TestCase):
    """Tests for Operation dataclass."""
    
    def test_operation_creation(self):
        """Test creating an Operation."""
        op = Operation(op_type=OperationType.SELECT, columns=["a", "b"])
        self.assertEqual(op.op_type, OperationType.SELECT)
        self.assertEqual(op.columns, ["a", "b"])
    
    def test_operation_with_details(self):
        """Test Operation with details."""
        op = Operation(
            op_type=OperationType.FILTER,
            details="age > 30"
        )
        self.assertEqual(op.details, "age > 30")


class TestLazyExecutionPlan(unittest.TestCase):
    """Tests for LazyExecutionPlan class."""
    
    def test_empty_plan(self):
        """Test empty execution plan."""
        plan = LazyExecutionPlan()
        self.assertEqual(len(plan.operations), 0)
    
    def test_add_operation(self):
        """Test adding operation to plan."""
        plan = LazyExecutionPlan()
        plan.add_operation(OperationType.SELECT, columns=["id", "name"])
        
        self.assertEqual(len(plan.operations), 1)
        self.assertEqual(plan.operations[0].op_type, OperationType.SELECT)
    
    def test_add_multiple_operations(self):
        """Test adding multiple operations."""
        plan = LazyExecutionPlan()
        plan.add_operation(OperationType.CREATE_DATAFRAME, num_rows=100)
        plan.add_operation(OperationType.FILTER, details="age > 30")
        plan.add_operation(OperationType.SELECT, columns=["name"])
        
        self.assertEqual(len(plan.operations), 3)
    
    def test_build_stages(self):
        """Test building stages from plan."""
        plan = LazyExecutionPlan()
        plan.add_operation(OperationType.CREATE_DATAFRAME, num_rows=100)
        plan.add_operation(OperationType.FILTER)
        plan.add_operation(OperationType.GROUP_BY)  # Causes shuffle
        plan.add_operation(OperationType.SHOW)
        
        stages = plan.build_stages(num_partitions=4)
        self.assertGreater(len(stages), 0)
    
    def test_explain(self):
        """Test explain method."""
        plan = LazyExecutionPlan()
        plan.add_operation(OperationType.CREATE_DATAFRAME, num_rows=10)
        plan.add_operation(OperationType.SELECT, columns=["a"])
        
        explanation = plan.explain()
        self.assertIsInstance(explanation, str)
        self.assertIn("SELECT", explanation.upper())


class TestJobMetrics(unittest.TestCase):
    """Tests for JobMetrics class."""
    
    def test_job_metrics_creation(self):
        """Test creating JobMetrics."""
        metrics = JobMetrics(job_id=1)
        self.assertEqual(metrics.job_id, 1)
        self.assertEqual(metrics.status, "pending")
    
    def test_job_duration(self):
        """Test job duration calculation."""
        import time
        metrics = JobMetrics(job_id=1)
        metrics.start_time = time.time()
        time.sleep(0.01)  # 10ms
        metrics.end_time = time.time()
        
        self.assertGreater(metrics.duration_ms, 0)
    
    def test_duration_str(self):
        """Test duration string formatting."""
        metrics = JobMetrics(job_id=1)
        metrics.start_time = 0
        metrics.end_time = 0.5  # 500ms
        
        duration_str = metrics.duration_str
        self.assertIn("ms", duration_str)


class TestExecutionEngine(unittest.TestCase):
    """Tests for ExecutionEngine class."""
    
    def test_engine_creation(self):
        """Test creating ExecutionEngine."""
        engine = ExecutionEngine(num_partitions=4, app_name="TestApp")
        self.assertEqual(engine.num_partitions, 4)
        self.assertEqual(engine.app_name, "TestApp")
    
    def test_job_counter(self):
        """Test job counter starts at 0."""
        engine = ExecutionEngine()
        self.assertEqual(engine.job_counter, 0)
    
    def test_empty_jobs_list(self):
        """Test jobs list starts empty."""
        engine = ExecutionEngine()
        self.assertEqual(len(engine.jobs), 0)
    
    def test_ui_callback_setter(self):
        """Test setting UI callback."""
        engine = ExecutionEngine()
        callback = lambda x: None
        engine.set_ui_callback(callback)
        self.assertEqual(engine._ui_callback, callback)
    
    def test_get_last_job_empty(self):
        """Test getting last job when empty."""
        engine = ExecutionEngine()
        self.assertIsNone(engine.get_last_job())
    
    def test_clear_jobs(self):
        """Test clearing jobs."""
        engine = ExecutionEngine()
        engine.job_counter = 5
        engine.jobs.append(JobMetrics(job_id=1))
        
        engine.clear_jobs()
        
        self.assertEqual(len(engine.jobs), 0)
        self.assertEqual(engine.job_counter, 0)


if __name__ == "__main__":
    unittest.main()
