"""
Spark UI - HTML-based Spark UI that mimics Apache Spark's Web UI.
"""
import os
import json
import time
import webbrowser
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime


@dataclass
class TaskMetrics:
    """Metrics for a single task."""
    task_id: int
    stage_id: int
    attempt: int = 0
    launch_time: float = 0
    finish_time: float = 0
    duration_ms: int = 0
    status: str = "SUCCESS"
    locality: str = "PROCESS_LOCAL"
    input_records: int = 0
    input_bytes: int = 0
    output_records: int = 0
    output_bytes: int = 0
    shuffle_read_bytes: int = 0
    shuffle_write_bytes: int = 0
    executor_id: str = "driver"
    host: str = "localhost"


@dataclass
class StageMetrics:
    """Metrics for a stage."""
    stage_id: int
    stage_name: str
    num_tasks: int = 4
    status: str = "COMPLETE"
    submitted_time: float = 0
    completion_time: float = 0
    duration_ms: int = 0
    input_records: int = 0
    input_bytes: int = 0
    output_records: int = 0
    output_bytes: int = 0
    shuffle_read_bytes: int = 0
    shuffle_write_bytes: int = 0
    tasks: List[TaskMetrics] = field(default_factory=list)


@dataclass
class JobMetrics:
    """Metrics for a job."""
    job_id: int
    job_name: str
    status: str = "RUNNING"
    submitted_time: float = 0
    completion_time: float = 0
    duration_ms: int = 0
    num_stages: int = 0
    num_tasks: int = 0
    num_completed_stages: int = 0
    num_completed_tasks: int = 0
    stages: List[StageMetrics] = field(default_factory=list)


class SparkUIServer:
    """HTTP server for Spark UI."""
    
    def __init__(self, port: int = 4040, ui_dir: str = None):
        self.port = port
        self.ui_dir = ui_dir or os.path.join(os.path.dirname(__file__), "spark_ui_static")
        self.server = None
        self.thread = None
        self._running = False
    
    def start(self):
        """Start the UI server."""
        os.makedirs(self.ui_dir, exist_ok=True)
        
        handler = lambda *args: SparkUIHandler(*args, directory=self.ui_dir)
        
        # Try to find an available port
        for attempt in range(10):
            try:
                self.server = HTTPServer(("localhost", self.port + attempt), handler)
                self.port = self.port + attempt
                break
            except OSError:
                continue
        
        self._running = True
        self.thread = threading.Thread(target=self._serve, daemon=True)
        self.thread.start()
        
        return self.port
    
    def _serve(self):
        """Serve requests."""
        while self._running:
            self.server.handle_request()
    
    def stop(self):
        """Stop the server."""
        self._running = False
        if self.server:
            self.server.shutdown()


class SparkUIHandler(SimpleHTTPRequestHandler):
    """Custom handler for Spark UI."""
    
    def __init__(self, *args, directory=None, **kwargs):
        self.directory = directory
        super().__init__(*args, **kwargs)
    
    def log_message(self, format, *args):
        """Suppress logging."""
        pass


class SparkUIGenerator:
    """
    Generates HTML Spark UI that mimics Apache Spark's Web UI design.
    """
    
    def __init__(self, app_name: str = "Spark Mock", output_dir: str = None):
        self.app_name = app_name
        self.output_dir = output_dir or os.path.join(os.getcwd(), ".spark_ui")
        self.jobs: List[JobMetrics] = []
        self.stages: List[StageMetrics] = []
        self.executors: List[Dict] = []
        self.environment: Dict = {}
        self._server: Optional[SparkUIServer] = None
        self._current_job: Optional[JobMetrics] = None
        self._job_counter = 0
        self._stage_counter = 0
        self._task_counter = 0
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialize with default executor
        self.executors = [{
            "id": "driver",
            "host": "localhost",
            "port": "0",
            "cores": 4,
            "memory": "1024 MB",
            "status": "Active"
        }]
    
    def start_job(self, job_name: str, num_stages: int = 1) -> int:
        """Start a new job."""
        job_id = self._job_counter
        self._job_counter += 1
        
        job = JobMetrics(
            job_id=job_id,
            job_name=job_name,
            status="RUNNING",
            submitted_time=time.time(),
            num_stages=num_stages
        )
        
        self._current_job = job
        self.jobs.append(job)
        
        return job_id
    
    def add_stage(self, stage_name: str, num_tasks: int = 4) -> int:
        """Add a stage to current job."""
        stage_id = self._stage_counter
        self._stage_counter += 1
        
        stage = StageMetrics(
            stage_id=stage_id,
            stage_name=stage_name,
            num_tasks=num_tasks,
            status="RUNNING",
            submitted_time=time.time()
        )
        
        # Add tasks
        for i in range(num_tasks):
            task = TaskMetrics(
                task_id=self._task_counter,
                stage_id=stage_id,
                launch_time=time.time()
            )
            self._task_counter += 1
            stage.tasks.append(task)
        
        self.stages.append(stage)
        
        if self._current_job:
            self._current_job.stages.append(stage)
            self._current_job.num_tasks += num_tasks
        
        return stage_id
    
    def complete_stage(self, stage_id: int, metrics: Dict = None):
        """Complete a stage."""
        for stage in self.stages:
            if stage.stage_id == stage_id:
                stage.status = "COMPLETE"
                stage.completion_time = time.time()
                stage.duration_ms = int((stage.completion_time - stage.submitted_time) * 1000)
                
                if metrics:
                    stage.input_records = metrics.get("input_records", 0)
                    stage.input_bytes = metrics.get("input_bytes", 0)
                    stage.output_records = metrics.get("output_records", 0)
                    stage.output_bytes = metrics.get("output_bytes", 0)
                    stage.shuffle_read_bytes = metrics.get("shuffle_read_bytes", 0)
                    stage.shuffle_write_bytes = metrics.get("shuffle_write_bytes", 0)
                
                # Complete all tasks
                for task in stage.tasks:
                    task.status = "SUCCESS"
                    task.finish_time = time.time()
                    task.duration_ms = int((task.finish_time - task.launch_time) * 1000)
                
                if self._current_job:
                    self._current_job.num_completed_stages += 1
                    self._current_job.num_completed_tasks += len(stage.tasks)
                
                break
    
    def complete_job(self, job_id: int, status: str = "SUCCEEDED"):
        """Complete a job."""
        for job in self.jobs:
            if job.job_id == job_id:
                job.status = status
                job.completion_time = time.time()
                job.duration_ms = int((job.completion_time - job.submitted_time) * 1000)
                break
        
        self._current_job = None
        self._generate_html()
    
    def _format_bytes(self, bytes_val: int) -> str:
        """Format bytes to human readable."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_val < 1024:
                return f"{bytes_val:.1f} {unit}"
            bytes_val /= 1024
        return f"{bytes_val:.1f} PB"
    
    def _format_time(self, timestamp: float) -> str:
        """Format timestamp."""
        if timestamp == 0:
            return "N/A"
        return datetime.fromtimestamp(timestamp).strftime("%Y/%m/%d %H:%M:%S")
    
    def _format_duration(self, ms: int) -> str:
        """Format duration."""
        if ms < 1000:
            return f"{ms} ms"
        elif ms < 60000:
            return f"{ms/1000:.1f} s"
        else:
            return f"{ms/60000:.1f} min"
    
    def _generate_html(self):
        """Generate all HTML files."""
        self._generate_index()
        self._generate_jobs_page()
        self._generate_stages_page()
        self._generate_executors_page()
        self._generate_css()
    
    def _generate_css(self):
        """Generate CSS file matching Spark UI style."""
        css = '''
/* Spark UI CSS - Authentic Apache Spark Style */
:root {
    --spark-blue: #1976d2;
    --spark-dark-blue: #0d47a1;
    --spark-light-blue: #e3f2fd;
    --spark-orange: #ff9800;
    --spark-green: #4caf50;
    --spark-red: #f44336;
    --spark-gray: #666;
    --spark-light-gray: #f5f5f5;
    --spark-border: #ddd;
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    font-size: 14px;
    line-height: 1.5;
    color: #333;
    background: #fff;
}

/* Header */
.navbar {
    background: linear-gradient(180deg, #4a4a4a 0%, #3a3a3a 100%);
    padding: 10px 20px;
    color: white;
    display: flex;
    align-items: center;
    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
}

.navbar-brand {
    display: flex;
    align-items: center;
    gap: 10px;
}

.navbar-brand img {
    height: 30px;
}

.navbar-brand h1 {
    font-size: 20px;
    font-weight: 500;
}

.navbar-nav {
    display: flex;
    list-style: none;
    margin-left: 40px;
    gap: 5px;
}

.navbar-nav a {
    color: white;
    text-decoration: none;
    padding: 8px 16px;
    border-radius: 4px;
    transition: background 0.2s;
}

.navbar-nav a:hover,
.navbar-nav a.active {
    background: rgba(255,255,255,0.15);
}

/* Container */
.container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 20px;
}

/* Page Header */
.page-header {
    margin-bottom: 20px;
    padding-bottom: 15px;
    border-bottom: 1px solid var(--spark-border);
}

.page-header h2 {
    font-size: 24px;
    font-weight: 500;
    color: #333;
}

/* Summary Box */
.summary-box {
    background: var(--spark-light-gray);
    border: 1px solid var(--spark-border);
    border-radius: 4px;
    padding: 15px;
    margin-bottom: 20px;
}

.summary-row {
    display: flex;
    gap: 40px;
    flex-wrap: wrap;
}

.summary-item {
    display: flex;
    gap: 8px;
}

.summary-item .label {
    font-weight: 500;
    color: var(--spark-gray);
}

.summary-item .value {
    color: #333;
}

/* Tables */
.table-container {
    overflow-x: auto;
    margin-bottom: 20px;
}

table {
    width: 100%;
    border-collapse: collapse;
    background: white;
}

th, td {
    padding: 10px 12px;
    text-align: left;
    border-bottom: 1px solid var(--spark-border);
}

th {
    background: var(--spark-light-gray);
    font-weight: 600;
    color: #333;
    white-space: nowrap;
}

tr:hover {
    background: #f8f9fa;
}

/* Status badges */
.badge {
    display: inline-block;
    padding: 3px 8px;
    border-radius: 3px;
    font-size: 12px;
    font-weight: 600;
}

.badge-success {
    background: #d4edda;
    color: #155724;
}

.badge-running {
    background: #cce5ff;
    color: #004085;
}

.badge-failed {
    background: #f8d7da;
    color: #721c24;
}

.badge-pending {
    background: #fff3cd;
    color: #856404;
}

/* Progress bar */
.progress {
    height: 18px;
    background: #e9ecef;
    border-radius: 3px;
    overflow: hidden;
    position: relative;
}

.progress-bar {
    height: 100%;
    background: var(--spark-green);
    transition: width 0.3s;
}

.progress-bar.running {
    background: var(--spark-blue);
}

.progress-text {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    font-size: 11px;
    font-weight: 600;
    color: #333;
}

/* Links */
a {
    color: var(--spark-blue);
    text-decoration: none;
}

a:hover {
    text-decoration: underline;
}

/* Section */
.section {
    margin-bottom: 30px;
}

.section-header {
    font-size: 18px;
    font-weight: 500;
    margin-bottom: 15px;
    padding-bottom: 10px;
    border-bottom: 2px solid var(--spark-blue);
}

/* Cards */
.card {
    background: white;
    border: 1px solid var(--spark-border);
    border-radius: 4px;
    margin-bottom: 20px;
}

.card-header {
    background: var(--spark-light-gray);
    padding: 12px 15px;
    border-bottom: 1px solid var(--spark-border);
    font-weight: 600;
}

.card-body {
    padding: 15px;
}

/* Metrics Grid */
.metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 15px;
    margin-bottom: 20px;
}

.metric-card {
    background: var(--spark-light-gray);
    border: 1px solid var(--spark-border);
    border-radius: 4px;
    padding: 15px;
    text-align: center;
}

.metric-value {
    font-size: 28px;
    font-weight: 600;
    color: var(--spark-blue);
}

.metric-label {
    font-size: 12px;
    color: var(--spark-gray);
    margin-top: 5px;
}

/* Timeline */
.timeline {
    position: relative;
    padding: 20px 0;
}

.timeline-item {
    display: flex;
    gap: 15px;
    margin-bottom: 15px;
}

.timeline-dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: var(--spark-blue);
    flex-shrink: 0;
    margin-top: 4px;
}

.timeline-content {
    flex: 1;
}

/* DAG Visualization */
.dag-container {
    background: #fafafa;
    border: 1px solid var(--spark-border);
    border-radius: 4px;
    padding: 20px;
    margin-bottom: 20px;
    overflow-x: auto;
}

.dag-node {
    display: inline-block;
    background: white;
    border: 2px solid var(--spark-blue);
    border-radius: 4px;
    padding: 10px 15px;
    margin: 5px;
    text-align: center;
}

.dag-node.completed {
    border-color: var(--spark-green);
    background: #e8f5e9;
}

.dag-arrow {
    display: inline-block;
    color: var(--spark-gray);
    margin: 0 10px;
}

/* Footer */
.footer {
    text-align: center;
    padding: 20px;
    color: var(--spark-gray);
    font-size: 12px;
    border-top: 1px solid var(--spark-border);
    margin-top: 40px;
}

/* Responsive */
@media (max-width: 768px) {
    .navbar-nav {
        margin-left: auto;
    }
    
    .summary-row {
        flex-direction: column;
        gap: 10px;
    }
}
'''
        with open(os.path.join(self.output_dir, "spark-ui.css"), "w") as f:
            f.write(css)
    
    def _generate_nav(self, active: str = "jobs") -> str:
        """Generate navigation bar."""
        nav_items = [
            ("Jobs", "index.html", "jobs"),
            ("Stages", "stages.html", "stages"),
            ("Executors", "executors.html", "executors"),
        ]
        
        items_html = ""
        for label, href, key in nav_items:
            active_class = "active" if key == active else ""
            items_html += f'<a href="{href}" class="{active_class}">{label}</a>\n'
        
        return f'''
<nav class="navbar">
    <div class="navbar-brand">
        <svg width="30" height="30" viewBox="0 0 100 100">
            <circle cx="50" cy="50" r="45" fill="#E25A1C"/>
            <text x="50" y="65" font-size="40" fill="white" text-anchor="middle" font-weight="bold">S</text>
        </svg>
        <h1>{self.app_name}</h1>
    </div>
    <ul class="navbar-nav">
        {items_html}
    </ul>
</nav>
'''
    
    def _generate_index(self):
        """Generate main index page (Jobs)."""
        self._generate_jobs_page()
    
    def _generate_jobs_page(self):
        """Generate jobs listing page."""
        # Calculate stats
        total_jobs = len(self.jobs)
        completed_jobs = len([j for j in self.jobs if j.status == "SUCCEEDED"])
        running_jobs = len([j for j in self.jobs if j.status == "RUNNING"])
        failed_jobs = len([j for j in self.jobs if j.status == "FAILED"])
        
        # Generate job rows
        job_rows = ""
        for job in reversed(self.jobs):
            status_class = {
                "SUCCEEDED": "badge-success",
                "RUNNING": "badge-running",
                "FAILED": "badge-failed"
            }.get(job.status, "badge-pending")
            
            progress = 0
            if job.num_stages > 0:
                progress = int((job.num_completed_stages / job.num_stages) * 100)
            
            job_rows += f'''
            <tr>
                <td><a href="job_{job.job_id}.html">{job.job_id}</a></td>
                <td>{job.job_name}</td>
                <td>{self._format_time(job.submitted_time)}</td>
                <td>{self._format_duration(job.duration_ms)}</td>
                <td>{job.num_completed_stages}/{job.num_stages}</td>
                <td>{job.num_completed_tasks}/{job.num_tasks}</td>
                <td>
                    <div class="progress">
                        <div class="progress-bar" style="width: {progress}%"></div>
                        <span class="progress-text">{progress}%</span>
                    </div>
                </td>
                <td><span class="badge {status_class}">{job.status}</span></td>
            </tr>
            '''
        
        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.app_name} - Spark Jobs</title>
    <link rel="stylesheet" href="spark-ui.css">
    <meta http-equiv="refresh" content="5">
</head>
<body>
    {self._generate_nav("jobs")}
    
    <div class="container">
        <div class="page-header">
            <h2>Spark Jobs</h2>
        </div>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-value">{total_jobs}</div>
                <div class="metric-label">Total Jobs</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" style="color: #4caf50">{completed_jobs}</div>
                <div class="metric-label">Completed</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" style="color: #1976d2">{running_jobs}</div>
                <div class="metric-label">Running</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" style="color: #f44336">{failed_jobs}</div>
                <div class="metric-label">Failed</div>
            </div>
        </div>
        
        <div class="section">
            <h3 class="section-header">Event Timeline</h3>
            <div class="dag-container">
                {"".join([f'<div class="dag-node completed">Job {j.job_id}</div><span class="dag-arrow">→</span>' for j in self.jobs[-5:]])}
            </div>
        </div>
        
        <div class="section">
            <h3 class="section-header">All Jobs ({total_jobs})</h3>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Job ID</th>
                            <th>Description</th>
                            <th>Submitted</th>
                            <th>Duration</th>
                            <th>Stages</th>
                            <th>Tasks</th>
                            <th>Progress</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {job_rows if job_rows else '<tr><td colspan="8" style="text-align: center; color: #666;">No jobs to display</td></tr>'}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    
    <footer class="footer">
        <p>Spark Mock UI - Powered by Polars | {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
    </footer>
</body>
</html>
'''
        
        with open(os.path.join(self.output_dir, "index.html"), "w") as f:
            f.write(html)
    
    def _generate_stages_page(self):
        """Generate stages listing page."""
        total_stages = len(self.stages)
        completed_stages = len([s for s in self.stages if s.status == "COMPLETE"])
        
        # Calculate total I/O
        total_input = sum(s.input_bytes for s in self.stages)
        total_output = sum(s.output_bytes for s in self.stages)
        total_shuffle_read = sum(s.shuffle_read_bytes for s in self.stages)
        total_shuffle_write = sum(s.shuffle_write_bytes for s in self.stages)
        
        # Generate stage rows
        stage_rows = ""
        for stage in reversed(self.stages):
            status_class = "badge-success" if stage.status == "COMPLETE" else "badge-running"
            
            stage_rows += f'''
            <tr>
                <td><a href="stage_{stage.stage_id}.html">{stage.stage_id}</a></td>
                <td>{stage.stage_name}</td>
                <td>{self._format_time(stage.submitted_time)}</td>
                <td>{self._format_duration(stage.duration_ms)}</td>
                <td>{len([t for t in stage.tasks if t.status == "SUCCESS"])}/{stage.num_tasks}</td>
                <td>{self._format_bytes(stage.input_bytes)}</td>
                <td>{self._format_bytes(stage.output_bytes)}</td>
                <td>{self._format_bytes(stage.shuffle_read_bytes)}</td>
                <td>{self._format_bytes(stage.shuffle_write_bytes)}</td>
                <td><span class="badge {status_class}">{stage.status}</span></td>
            </tr>
            '''
        
        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.app_name} - Stages</title>
    <link rel="stylesheet" href="spark-ui.css">
    <meta http-equiv="refresh" content="5">
</head>
<body>
    {self._generate_nav("stages")}
    
    <div class="container">
        <div class="page-header">
            <h2>Stages</h2>
        </div>
        
        <div class="summary-box">
            <div class="summary-row">
                <div class="summary-item">
                    <span class="label">Total Stages:</span>
                    <span class="value">{total_stages}</span>
                </div>
                <div class="summary-item">
                    <span class="label">Completed:</span>
                    <span class="value">{completed_stages}</span>
                </div>
                <div class="summary-item">
                    <span class="label">Input:</span>
                    <span class="value">{self._format_bytes(total_input)}</span>
                </div>
                <div class="summary-item">
                    <span class="label">Output:</span>
                    <span class="value">{self._format_bytes(total_output)}</span>
                </div>
                <div class="summary-item">
                    <span class="label">Shuffle Read:</span>
                    <span class="value">{self._format_bytes(total_shuffle_read)}</span>
                </div>
                <div class="summary-item">
                    <span class="label">Shuffle Write:</span>
                    <span class="value">{self._format_bytes(total_shuffle_write)}</span>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h3 class="section-header">All Stages</h3>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Stage ID</th>
                            <th>Description</th>
                            <th>Submitted</th>
                            <th>Duration</th>
                            <th>Tasks</th>
                            <th>Input</th>
                            <th>Output</th>
                            <th>Shuffle Read</th>
                            <th>Shuffle Write</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {stage_rows if stage_rows else '<tr><td colspan="10" style="text-align: center; color: #666;">No stages to display</td></tr>'}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    
    <footer class="footer">
        <p>Spark Mock UI - Powered by Polars | {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
    </footer>
</body>
</html>
'''
        
        with open(os.path.join(self.output_dir, "stages.html"), "w") as f:
            f.write(html)
    
    def _generate_executors_page(self):
        """Generate executors page."""
        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.app_name} - Executors</title>
    <link rel="stylesheet" href="spark-ui.css">
    <meta http-equiv="refresh" content="5">
</head>
<body>
    {self._generate_nav("executors")}
    
    <div class="container">
        <div class="page-header">
            <h2>Executors</h2>
        </div>
        
        <div class="summary-box">
            <div class="summary-row">
                <div class="summary-item">
                    <span class="label">Active Executors:</span>
                    <span class="value">{len(self.executors)}</span>
                </div>
                <div class="summary-item">
                    <span class="label">Total Cores:</span>
                    <span class="value">{sum(e.get('cores', 0) for e in self.executors)}</span>
                </div>
                <div class="summary-item">
                    <span class="label">Total Memory:</span>
                    <span class="value">{sum(int(e.get('memory', '0').split()[0]) for e in self.executors)} MB</span>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h3 class="section-header">Executor Summary</h3>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Executor ID</th>
                            <th>Address</th>
                            <th>Status</th>
                            <th>Cores</th>
                            <th>Memory</th>
                            <th>Active Tasks</th>
                            <th>Failed Tasks</th>
                            <th>Complete Tasks</th>
                        </tr>
                    </thead>
                    <tbody>
                        {self._generate_executor_rows()}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    
    <footer class="footer">
        <p>Spark Mock UI - Powered by Polars | {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
    </footer>
</body>
</html>
'''
        
        with open(os.path.join(self.output_dir, "executors.html"), "w") as f:
            f.write(html)
    
    def _generate_executor_rows(self) -> str:
        """Generate executor table rows."""
        rows = ""
        for executor in self.executors:
            rows += f'''
            <tr>
                <td>{executor.get('id', 'N/A')}</td>
                <td>{executor.get('host', 'localhost')}:{executor.get('port', '0')}</td>
                <td><span class="badge badge-success">{executor.get('status', 'Active')}</span></td>
                <td>{executor.get('cores', 0)}</td>
                <td>{executor.get('memory', 'N/A')}</td>
                <td>0</td>
                <td>0</td>
                <td>{self._task_counter}</td>
            </tr>
            '''
        return rows
    
    def open_browser(self):
        """Open the Spark UI in a browser."""
        index_path = os.path.join(self.output_dir, "index.html")
        if os.path.exists(index_path):
            webbrowser.open(f"file://{index_path}")
    
    def start_server(self, port: int = 4040) -> int:
        """Start HTTP server and return port."""
        self._server = SparkUIServer(port=port, ui_dir=self.output_dir)
        actual_port = self._server.start()
        print(f"Spark UI available at http://localhost:{actual_port}")
        return actual_port
    
    def stop_server(self):
        """Stop the HTTP server."""
        if self._server:
            self._server.stop()
