# performance_metrics.py
import time
from typing import Dict
from models import PerformanceMetrics as PerformanceMetricsModel


class PerformanceMetrics:
    """Coleta e gerencia métricas de performance do sistema."""
    
    def __init__(self):
        self.metrics = {
            "total_requests": 0,
            "successful_classifications": 0,
            "average_processing_time": 0.0,
            "error_count": 0,
            "last_updated": time.time()
        }

    def record_request(self, processing_time: float, success: bool = True):
        """Record metrics for each request."""
        self.metrics["total_requests"] += 1
        self.metrics["last_updated"] = time.time()

        if success:
            self.metrics["successful_classifications"] += 1
            total = self.metrics["successful_classifications"]
            current_avg = self.metrics["average_processing_time"]
            self.metrics["average_processing_time"] = (
                (current_avg * (total - 1) + processing_time) / total
            )
        else:
            self.metrics["error_count"] += 1

    def get_metrics(self) -> Dict:
        """Return a copy of current metrics."""
        return PerformanceMetricsModel(**self.metrics).dict()