import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum
from azure.identity import DefaultAzureCredential
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry import metrics, trace
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPTraceExporter
from opentelemetry.sdk.resources import Resource
from pythonjsonlogger import jsonlogger


class EventSeverity(str, Enum):
    """Monitoring event severity levels"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class MonitoringMetrics:
    """Application monitoring metrics definitions"""
    
    def __init__(self, instrumentation_key: Optional[str] = None):
        """
        Initialize monitoring metrics
        
        Args:
            instrumentation_key: Application Insights instrumentation key
        """
        self.instrumentation_key = instrumentation_key or os.getenv("APPINSIGHTS_INSTRUMENTATION_KEY")
        self.enabled = os.getenv("MONITORING_ENABLED", "true").lower() == "true"
        
        if self.enabled and self.instrumentation_key:
            self._configure_azure_monitor()
    
    def _configure_azure_monitor(self):
        """Configure Azure Monitor/Application Insights"""
        try:
            configure_azure_monitor(
                credential=DefaultAzureCredential(),
                instrumentation_key=self.instrumentation_key,
            )
        except Exception as e:
            logging.warning(f"Failed to configure Azure Monitor: {e}")
    
    def record_request(self, method: str, path: str, status_code: int, duration_ms: float):
        """Record HTTP request metric"""
        if not self.enabled:
            return
        
        try:
            tracer = trace.get_tracer(__name__)
            with tracer.start_as_current_span("http_request") as span:
                span.set_attribute("http.method", method)
                span.set_attribute("http.url", path)
                span.set_attribute("http.status_code", status_code)
                span.set_attribute("http.duration_ms", duration_ms)
        except Exception as e:
            logging.warning(f"Failed to record request metric: {e}")
    
    def record_database_operation(self, operation: str, duration_ms: float, success: bool):
        """Record database operation metric"""
        if not self.enabled:
            return
        
        try:
            tracer = trace.get_tracer(__name__)
            with tracer.start_as_current_span("db_operation") as span:
                span.set_attribute("db.operation", operation)
                span.set_attribute("db.duration_ms", duration_ms)
                span.set_attribute("db.success", success)
        except Exception as e:
            logging.warning(f"Failed to record database metric: {e}")
    
    def record_authentication(self, user_email: str, success: bool, method: str = "jwt"):
        """Record authentication attempt"""
        if not self.enabled:
            return
        
        try:
            tracer = trace.get_tracer(__name__)
            with tracer.start_as_current_span("authentication") as span:
                # Mask email in trace (privacy)
                masked_email = f"{user_email.split('@')[0][:2]}***@{user_email.split('@')[1]}"
                span.set_attribute("auth.user", masked_email)
                span.set_attribute("auth.success", success)
                span.set_attribute("auth.method", method)
        except Exception as e:
            logging.warning(f"Failed to record auth metric: {e}")
    
    def record_error(self, error_type: str, error_message: str, severity: EventSeverity):
        """Record error event"""
        if not self.enabled:
            return
        
        try:
            tracer = trace.get_tracer(__name__)
            with tracer.start_as_current_span("error") as span:
                span.set_attribute("error.type", error_type)
                span.set_attribute("error.message", error_message)
                span.set_attribute("error.severity", severity.value)
        except Exception as e:
            logging.warning(f"Failed to record error metric: {e}")


class StructuredLogger:
    """Structured JSON logging for Application Insights integration"""
    
    def __init__(self, name: str):
        """Initialize structured logger"""
        self.logger = logging.getLogger(name)
        self.logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))
        
        # Console handler with JSON formatting
        console_handler = logging.StreamHandler()
        json_formatter = jsonlogger.JsonFormatter(
            fmt="%(timestamp)s %(level)s %(name)s %(message)s",
            rename_fields={"timestamp": "time"}
        )
        console_handler.setFormatter(json_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler (optional)
        if os.getenv("LOG_FILE"):
            file_handler = logging.FileHandler(os.getenv("LOG_FILE"))
            file_handler.setFormatter(json_formatter)
            self.logger.addHandler(file_handler)
    
    def log_request(self, method: str, path: str, status_code: int, duration_ms: float):
        """Log HTTP request"""
        self.logger.info("http_request", extra={
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": duration_ms
        })
    
    def log_database_operation(self, operation: str, duration_ms: float, success: bool):
        """Log database operation"""
        self.logger.info("database_operation", extra={
            "operation": operation,
            "duration_ms": duration_ms,
            "success": success
        })
    
    def log_authentication(self, user_email: str, success: bool):
        """Log authentication attempt"""
        masked_email = f"{user_email.split('@')[0][:2]}***@{user_email.split('@')[1]}"
        self.logger.info("authentication", extra={
            "user": masked_email,
            "success": success
        })
    
    def log_error(self, error_type: str, error_message: str, severity: EventSeverity):
        """Log error event"""
        log_level = {
            EventSeverity.CRITICAL: logging.CRITICAL,
            EventSeverity.HIGH: logging.ERROR,
            EventSeverity.MEDIUM: logging.WARNING,
            EventSeverity.LOW: logging.INFO,
            EventSeverity.INFO: logging.DEBUG,
        }.get(severity, logging.INFO)
        
        self.logger.log(log_level, "error_event", extra={
            "error_type": error_type,
            "error_message": error_message,
            "severity": severity.value
        })


# Global monitoring instance
monitoring = MonitoringMetrics()
logger = StructuredLogger(__name__)
