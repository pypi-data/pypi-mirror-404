"""
Unit tests for HTML UI generator.
"""
import unittest
import tempfile
import os
import shutil

from spark_mock.ui.html_ui import (
    SparkUIGenerator, TaskMetrics, StageMetrics, JobMetrics
)


class TestTaskMetrics(unittest.TestCase):
    """Tests for TaskMetrics dataclass."""
    
    def test_task_metrics_creation(self):
        """Test creating TaskMetrics."""
        task = TaskMetrics(task_id=1, stage_id=0)
        self.assertEqual(task.task_id, 1)
        self.assertEqual(task.stage_id, 0)
        self.assertEqual(task.status, "SUCCESS")
    
    def test_task_metrics_defaults(self):
        """Test TaskMetrics default values."""
        task = TaskMetrics(task_id=0, stage_id=0)
        self.assertEqual(task.attempt, 0)
        self.assertEqual(task.locality, "PROCESS_LOCAL")
        self.assertEqual(task.executor_id, "driver")


class TestStageMetrics(unittest.TestCase):
    """Tests for StageMetrics dataclass."""
    
    def test_stage_metrics_creation(self):
        """Test creating StageMetrics."""
        stage = StageMetrics(stage_id=0, stage_name="Stage 0")
        self.assertEqual(stage.stage_id, 0)
        self.assertEqual(stage.stage_name, "Stage 0")
        self.assertEqual(stage.status, "COMPLETE")
    
    def test_stage_metrics_defaults(self):
        """Test StageMetrics default values."""
        stage = StageMetrics(stage_id=0, stage_name="Test")
        self.assertEqual(stage.num_tasks, 4)
        self.assertEqual(len(stage.tasks), 0)


class TestJobMetricsUI(unittest.TestCase):
    """Tests for UI JobMetrics dataclass."""
    
    def test_job_metrics_creation(self):
        """Test creating JobMetrics."""
        job = JobMetrics(job_id=1, job_name="Test Job")
        self.assertEqual(job.job_id, 1)
        self.assertEqual(job.job_name, "Test Job")
        self.assertEqual(job.status, "RUNNING")
    
    def test_job_metrics_defaults(self):
        """Test JobMetrics default values."""
        job = JobMetrics(job_id=0, job_name="Test")
        self.assertEqual(job.num_stages, 0)
        self.assertEqual(job.num_tasks, 0)
        self.assertEqual(len(job.stages), 0)


class TestSparkUIGenerator(unittest.TestCase):
    """Tests for SparkUIGenerator class."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.ui = SparkUIGenerator(app_name="TestApp", output_dir=self.temp_dir)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_init(self):
        """Test SparkUIGenerator initialization."""
        self.assertEqual(self.ui.app_name, "TestApp")
        self.assertEqual(self.ui.output_dir, self.temp_dir)
        self.assertEqual(len(self.ui.jobs), 0)
    
    def test_default_executor(self):
        """Test default executor is created."""
        self.assertEqual(len(self.ui.executors), 1)
        self.assertEqual(self.ui.executors[0]["id"], "driver")
    
    def test_start_job(self):
        """Test starting a job."""
        job_id = self.ui.start_job("Test Job", num_stages=2)
        self.assertEqual(job_id, 0)
        self.assertEqual(len(self.ui.jobs), 1)
        self.assertEqual(self.ui.jobs[0].job_name, "Test Job")
    
    def test_add_stage(self):
        """Test adding a stage."""
        self.ui.start_job("Test Job")
        stage_id = self.ui.add_stage("Stage 0", num_tasks=4)
        self.assertEqual(stage_id, 0)
        self.assertEqual(len(self.ui.stages), 1)
    
    def test_complete_stage(self):
        """Test completing a stage."""
        self.ui.start_job("Test Job")
        stage_id = self.ui.add_stage("Stage 0")
        
        metrics = {"input_records": 100, "output_records": 100}
        self.ui.complete_stage(stage_id, metrics)
        
        self.assertEqual(self.ui.stages[0].status, "COMPLETE")
        self.assertEqual(self.ui.stages[0].input_records, 100)
    
    def test_complete_job(self):
        """Test completing a job."""
        job_id = self.ui.start_job("Test Job")
        self.ui.add_stage("Stage 0")
        self.ui.complete_job(job_id, "SUCCEEDED")
        
        self.assertEqual(self.ui.jobs[0].status, "SUCCEEDED")
    
    def test_format_bytes(self):
        """Test bytes formatting."""
        self.assertEqual(self.ui._format_bytes(0), "0.0 B")
        self.assertEqual(self.ui._format_bytes(500), "500.0 B")
        self.assertEqual(self.ui._format_bytes(1024), "1.0 KB")
        self.assertEqual(self.ui._format_bytes(1024 * 1024), "1.0 MB")
    
    def test_format_duration(self):
        """Test duration formatting."""
        self.assertEqual(self.ui._format_duration(500), "500 ms")
        self.assertEqual(self.ui._format_duration(1500), "1.5 s")
        self.assertEqual(self.ui._format_duration(90000), "1.5 min")


class TestHTMLGeneration(unittest.TestCase):
    """Tests for HTML file generation."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.ui = SparkUIGenerator(app_name="TestApp", output_dir=self.temp_dir)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_generate_css(self):
        """Test CSS file generation."""
        self.ui._generate_css()
        css_path = os.path.join(self.temp_dir, "spark-ui.css")
        self.assertTrue(os.path.exists(css_path))
        
        with open(css_path) as f:
            content = f.read()
            self.assertIn("--spark-blue", content)
    
    def test_generate_jobs_page(self):
        """Test jobs page generation."""
        self.ui.start_job("Test Job")
        self.ui._generate_jobs_page()
        
        index_path = os.path.join(self.temp_dir, "index.html")
        self.assertTrue(os.path.exists(index_path))
        
        with open(index_path) as f:
            content = f.read()
            self.assertIn("Spark Jobs", content)
            self.assertIn("TestApp", content)
    
    def test_generate_stages_page(self):
        """Test stages page generation."""
        self.ui.start_job("Test")
        self.ui.add_stage("Stage 0")
        self.ui._generate_stages_page()
        
        stages_path = os.path.join(self.temp_dir, "stages.html")
        self.assertTrue(os.path.exists(stages_path))
    
    def test_generate_executors_page(self):
        """Test executors page generation."""
        self.ui._generate_executors_page()
        
        executors_path = os.path.join(self.temp_dir, "executors.html")
        self.assertTrue(os.path.exists(executors_path))
        
        with open(executors_path) as f:
            content = f.read()
            self.assertIn("Executors", content)
            self.assertIn("driver", content)
    
    def test_generate_nav(self):
        """Test navigation generation."""
        nav = self.ui._generate_nav("jobs")
        self.assertIn("Jobs", nav)
        self.assertIn("Stages", nav)
        self.assertIn("Executors", nav)
        self.assertIn("active", nav)


class TestFullWorkflow(unittest.TestCase):
    """Tests for full UI workflow."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.ui = SparkUIGenerator(app_name="WorkflowTest", output_dir=self.temp_dir)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_complete_workflow(self):
        """Test complete job workflow."""
        # Start job
        job_id = self.ui.start_job("Complete Workflow Test", num_stages=2)
        
        # Add stages
        stage0 = self.ui.add_stage("Read Data", num_tasks=4)
        stage1 = self.ui.add_stage("Process Data", num_tasks=4)
        
        # Complete stages with metrics
        self.ui.complete_stage(stage0, {
            "input_records": 1000,
            "output_records": 1000,
            "shuffle_read_bytes": 0,
            "shuffle_write_bytes": 10240
        })
        
        self.ui.complete_stage(stage1, {
            "input_records": 1000,
            "output_records": 100,
            "shuffle_read_bytes": 10240,
            "shuffle_write_bytes": 1024
        })
        
        # Complete job
        self.ui.complete_job(job_id, "SUCCEEDED")
        
        # Verify files exist
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, "index.html")))
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, "stages.html")))
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, "spark-ui.css")))
        
        # Verify job completed
        self.assertEqual(self.ui.jobs[0].status, "SUCCEEDED")
        self.assertEqual(len(self.ui.stages), 2)


if __name__ == "__main__":
    unittest.main()
