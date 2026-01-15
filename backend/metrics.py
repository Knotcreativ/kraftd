"""Metrics collection and monitoring for Kraftd Docs Backend."""
import time
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import json

logger = logging.getLogger(__name__)

class MetricType(Enum):
    """Metric types."""
    REQUEST = "request"
    EXTRACTION = "extraction"
    ERROR = "error"
    LATENCY = "latency"

@dataclass
class Metric:
    """Single metric data point."""
    timestamp: str
    metric_type: str
    endpoint: str
    status_code: int
    duration_ms: float
    document_id: Optional[str] = None
    error: Optional[str] = None
    details: Optional[Dict] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)

class MetricsCollector:
    """Collect and track metrics."""
    
    def __init__(self, max_metrics: int = 10000):
        """Initialize metrics collector."""
        self.metrics: List[Metric] = []
        self.max_metrics = max_metrics
        self.start_time = datetime.now()
        logger.info(f"Metrics collector initialized (max {max_metrics} metrics)")
    
    def record_request(self, endpoint: str, status_code: int, duration_ms: float, document_id: Optional[str] = None):
        """Record a request metric."""
        metric = Metric(
            timestamp=datetime.now().isoformat(),
            metric_type=MetricType.REQUEST.value,
            endpoint=endpoint,
            status_code=status_code,
            duration_ms=duration_ms,
            document_id=document_id
        )
        self._add_metric(metric)
    
    def record_extraction(self, document_id: str, status_code: int, duration_ms: float, 
                         completeness: float, quality: float, doc_type: str):
        """Record an extraction metric."""
        metric = Metric(
            timestamp=datetime.now().isoformat(),
            metric_type=MetricType.EXTRACTION.value,
            endpoint="/extract",
            status_code=status_code,
            duration_ms=duration_ms,
            document_id=document_id,
            details={
                "completeness": completeness,
                "quality": quality,
                "document_type": doc_type
            }
        )
        self._add_metric(metric)
    
    def record_error(self, endpoint: str, error: str, document_id: Optional[str] = None):
        """Record an error metric."""
        metric = Metric(
            timestamp=datetime.now().isoformat(),
            metric_type=MetricType.ERROR.value,
            endpoint=endpoint,
            status_code=500,
            duration_ms=0,
            document_id=document_id,
            error=error
        )
        self._add_metric(metric)
    
    def _add_metric(self, metric: Metric):
        """Add metric to collection."""
        self.metrics.append(metric)
        if len(self.metrics) > self.max_metrics:
            # Keep only recent metrics
            self.metrics = self.metrics[-self.max_metrics:]
    
    def get_stats(self) -> Dict:
        """Get aggregated statistics."""
        if not self.metrics:
            return {
                "total_requests": 0,
                "total_errors": 0,
                "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
                "avg_response_time_ms": 0,
                "error_rate": 0,
            }
        
        total_requests = len(self.metrics)
        error_metrics = [m for m in self.metrics if m.metric_type == MetricType.ERROR.value]
        request_metrics = [m for m in self.metrics if m.metric_type in [MetricType.REQUEST.value, MetricType.EXTRACTION.value]]
        
        avg_response_time = sum(m.duration_ms for m in request_metrics) / len(request_metrics) if request_metrics else 0
        error_rate = len(error_metrics) / total_requests if total_requests > 0 else 0
        
        # Extraction metrics
        extraction_metrics = [m for m in self.metrics if m.metric_type == MetricType.EXTRACTION.value]
        avg_completeness = sum(m.details["completeness"] for m in extraction_metrics if m.details) / len(extraction_metrics) if extraction_metrics else 0
        avg_quality = sum(m.details["quality"] for m in extraction_metrics if m.details) / len(extraction_metrics) if extraction_metrics else 0
        
        return {
            "total_requests": total_requests,
            "total_errors": len(error_metrics),
            "successful_requests": total_requests - len(error_metrics),
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
            "avg_response_time_ms": round(avg_response_time, 2),
            "error_rate": round(error_rate * 100, 2),
            "extraction_metrics": {
                "total_extractions": len(extraction_metrics),
                "avg_completeness": round(avg_completeness, 2),
                "avg_quality": round(avg_quality, 2),
            },
            "endpoint_stats": self._get_endpoint_stats()
        }
    
    def _get_endpoint_stats(self) -> Dict:
        """Get statistics by endpoint."""
        stats: Dict[str, Dict] = {}
        
        for metric in self.metrics:
            endpoint = metric.endpoint
            if endpoint not in stats:
                stats[endpoint] = {
                    "count": 0,
                    "avg_duration_ms": 0,
                    "errors": 0,
                    "total_duration": 0
                }
            
            stats[endpoint]["count"] += 1
            stats[endpoint]["total_duration"] += metric.duration_ms
            if metric.status_code >= 400:
                stats[endpoint]["errors"] += 1
        
        # Calculate averages
        for endpoint in stats:
            count = stats[endpoint]["count"]
            if count > 0:
                stats[endpoint]["avg_duration_ms"] = round(stats[endpoint]["total_duration"] / count, 2)
            del stats[endpoint]["total_duration"]
        
        return stats
    
    def get_metrics(self, limit: Optional[int] = None) -> List[Dict]:
        """Get recent metrics."""
        metrics = self.metrics[-limit:] if limit else self.metrics
        return [m.to_dict() for m in metrics]
    
    def export_metrics(self, filepath: str):
        """Export metrics to JSON file."""
        try:
            with open(filepath, 'w') as f:
                json.dump({
                    "exported_at": datetime.now().isoformat(),
                    "stats": self.get_stats(),
                    "recent_metrics": self.get_metrics(limit=100)
                }, f, indent=2)
            logger.info(f"Metrics exported to {filepath}")
        except Exception as e:
            logger.error(f"Failed to export metrics: {str(e)}")

# Global metrics instance
metrics_collector = MetricsCollector()
