"""
DevOps Info Service
Main application module using FastAPI framework
"""
import os
import sys
import socket
import platform
import logging
from threading import Lock
from time import perf_counter
from datetime import datetime, timezone
from typing import Dict, Any

from fastapi import FastAPI, Request
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
from pythonjsonlogger import jsonlogger

# Configure JSON logging
class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter for structured logging"""
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        log_record['timestamp'] = datetime.now(timezone.utc).isoformat()
        log_record['level'] = record.levelname
        log_record['logger'] = record.name
        log_record['module'] = record.module
        log_record['function'] = record.funcName

# Setup logging
logger = logging.getLogger("devops-info-service")
logger.setLevel(os.getenv('LOG_LEVEL', 'INFO'))

# JSON handler for stdout
json_handler = logging.StreamHandler(sys.stdout)
formatter = CustomJsonFormatter('%(timestamp)s %(level)s %(name)s %(message)s')
json_handler.setFormatter(formatter)
logger.addHandler(json_handler)

# Application startup time
start_time = datetime.now(timezone.utc)
visits_lock = Lock()

# Persistent visits counter configuration
DEFAULT_DATA_DIR = os.getenv('DATA_DIR', '/data')
DEFAULT_VISITS_FILE = os.getenv('VISITS_FILE', os.path.join(DEFAULT_DATA_DIR, 'visits'))

# Prometheus metrics (RED method + app-specific metrics)
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
)

http_requests_in_progress = Gauge(
    "http_requests_in_progress",
    "HTTP requests currently being processed",
)

devops_info_endpoint_calls_total = Counter(
    "devops_info_endpoint_calls_total",
    "Endpoint calls for DevOps info service",
    ["endpoint"],
)

devops_info_system_collection_seconds = Histogram(
    "devops_info_system_collection_seconds",
    "Time spent collecting system information",
)

# Configuration from environment variables
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Initialize FastAPI application
app = FastAPI(
    title="DevOps Info Service",
    description="DevOps course info service providing system and runtime information",
    version="1.0.0"
)

# Log application startup
logger.info("Application starting", extra={
    "host": HOST,
    "port": PORT,
    "debug": DEBUG,
    "python_version": platform.python_version()
})

# Middleware for logging HTTP requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests and responses"""
    request_start = perf_counter()

    # Log incoming request
    logger.info("HTTP Request", extra={
        "method": request.method,
        "path": request.url.path,
        "client_ip": request.client.host if request.client else "unknown",
        "user_agent": request.headers.get('user-agent', 'unknown')
    })

    http_requests_in_progress.inc()
    response = None
    try:
        # Process request
        response = await call_next(request)
        return response
    finally:
        endpoint = request.url.path
        route = request.scope.get("route")
        if route and hasattr(route, "path"):
            endpoint = route.path

        status_code = response.status_code if response else 500
        duration = perf_counter() - request_start

        http_requests_total.labels(
            method=request.method,
            endpoint=endpoint,
            status_code=str(status_code),
        ).inc()
        http_request_duration_seconds.labels(
            method=request.method,
            endpoint=endpoint,
        ).observe(duration)
        http_requests_in_progress.dec()

        logger.info("HTTP Response", extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": status_code,
            "duration_seconds": round(duration, 6),
        })


def get_uptime() -> Dict[str, Any]:
    """Calculate application uptime since start."""
    delta = datetime.now(timezone.utc) - start_time
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return {
        'seconds': seconds,
        'human': f"{hours} hours, {minutes} minutes"
    }


def get_system_info() -> Dict[str, Any]:
    """Get comprehensive system information."""
    return {
        'hostname': socket.gethostname(),
        'platform': platform.system(),
        'platform_version': platform.version(),
        'architecture': platform.machine(),
        'cpu_count': os.cpu_count(),
        'python_version': platform.python_version()
    }


def get_visits_file_path() -> str:
    """Get visits file path from environment with a safe default."""
    return os.getenv('VISITS_FILE', DEFAULT_VISITS_FILE)


def _atomic_write_text(file_path: str, content: str) -> None:
    """Write file content atomically to avoid partial updates."""
    temp_file_path = f"{file_path}.tmp"
    with open(temp_file_path, 'w', encoding='utf-8') as temp_file:
        temp_file.write(content)
    os.replace(temp_file_path, file_path)


def _ensure_visits_storage(visits_file_path: str) -> None:
    """Ensure visits counter file exists and contains a valid integer."""
    visits_dir = os.path.dirname(visits_file_path)
    if visits_dir:
        os.makedirs(visits_dir, exist_ok=True)

    if not os.path.exists(visits_file_path):
        _atomic_write_text(visits_file_path, '0\n')
        logger.info('Visits counter initialized', extra={
            'visits_file': visits_file_path,
            'visits_count': 0,
        })
        return

    try:
        with open(visits_file_path, 'r', encoding='utf-8') as visits_file:
            int((visits_file.read().strip() or '0'))
    except (OSError, ValueError):
        logger.warning('Visits counter file was invalid and has been reset', extra={
            'visits_file': visits_file_path,
        })
        _atomic_write_text(visits_file_path, '0\n')


def get_visits_count() -> int:
    """Read current visits count from persistent storage."""
    visits_file_path = get_visits_file_path()

    with visits_lock:
        _ensure_visits_storage(visits_file_path)
        try:
            with open(visits_file_path, 'r', encoding='utf-8') as visits_file:
                return int((visits_file.read().strip() or '0'))
        except (OSError, ValueError):
            logger.warning('Visits counter read failed, resetting to 0', extra={
                'visits_file': visits_file_path,
            })
            _atomic_write_text(visits_file_path, '0\n')
            return 0


def increment_visits_count() -> int:
    """Increment visits count and persist the new value."""
    visits_file_path = get_visits_file_path()

    with visits_lock:
        _ensure_visits_storage(visits_file_path)

        try:
            with open(visits_file_path, 'r', encoding='utf-8') as visits_file:
                current_count = int((visits_file.read().strip() or '0'))
        except (OSError, ValueError):
            logger.warning('Visits counter read failed during increment, resetting to 0', extra={
                'visits_file': visits_file_path,
            })
            current_count = 0

        new_count = current_count + 1
        _atomic_write_text(visits_file_path, f'{new_count}\n')
        return new_count


@app.get("/")
async def root(request: Request) -> Dict[str, Any]:
    """
    Main endpoint returning comprehensive service and system information.
    
    Returns:
        Dict containing service, system, runtime, request info and available endpoints
    """
    devops_info_endpoint_calls_total.labels(endpoint="/").inc()
    visits_count = increment_visits_count()

    system_info_start = perf_counter()
    system_info = get_system_info()
    devops_info_system_collection_seconds.observe(perf_counter() - system_info_start)

    uptime = get_uptime()
    
    return {
        "service": {
            "name": "devops-info-service",
            "version": "1.0.0",
            "description": "DevOps course info service",
            "framework": "FastAPI"
        },
        "system": system_info,
        "runtime": {
            "uptime_seconds": uptime['seconds'],
            "uptime_human": uptime['human'],
            "current_time": datetime.now(timezone.utc).isoformat(),
            "timezone": "UTC",
            "visits": visits_count
        },
        "request": {
            "client_ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get('user-agent', 'unknown'),
            "method": request.method,
            "path": request.url.path
        },
        "endpoints": [
            {
                "path": "/",
                "method": "GET",
                "description": "Service information"
            },
            {
                "path": "/health",
                "method": "GET",
                "description": "Health check"
            },
            {
                "path": "/metrics",
                "method": "GET",
                "description": "Prometheus metrics"
            },
            {
                "path": "/visits",
                "method": "GET",
                "description": "Current visits counter"
            }
        ]
    }


@app.get("/health")
async def health() -> Dict[str, Any]:
    """
    Health check endpoint for monitoring and Kubernetes probes.
    
    Returns:
        Dict containing health status, timestamp and uptime
    """
    devops_info_endpoint_calls_total.labels(endpoint="/health").inc()

    uptime = get_uptime()
    
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": uptime['seconds']
    }


@app.get("/metrics")
async def metrics() -> Response:
    """Prometheus metrics endpoint."""
    devops_info_endpoint_calls_total.labels(endpoint="/metrics").inc()
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/visits")
async def visits() -> Dict[str, Any]:
    """Return current visits counter value from persistent storage."""
    devops_info_endpoint_calls_total.labels(endpoint="/visits").inc()
    return {
        'visits': get_visits_count(),
        'visits_file': get_visits_file_path(),
    }


# Startup event
@app.on_event("startup")
async def startup_event():
    """Log application startup"""
    visits_file_path = get_visits_file_path()
    with visits_lock:
        _ensure_visits_storage(visits_file_path)

    logger.info("Application started successfully", extra={
        "service": "devops-info-service",
        "version": "1.0.0",
        "startup_time": start_time.isoformat(),
        "visits_file": visits_file_path,
    })


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Log application shutdown"""
    uptime = get_uptime()
    logger.info("Application shutting down", extra={
        "uptime_seconds": uptime['seconds'],
        "uptime_human": uptime['human']
    })


# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Log all unhandled exceptions"""
    logger.error("Unhandled exception", extra={
        "exception_type": type(exc).__name__,
        "exception_message": str(exc),
        "path": request.url.path,
        "method": request.method
    }, exc_info=True)
    
    return {
        "error": "Internal server error",
        "message": str(exc)
    }


if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting uvicorn server", extra={
        "host": HOST,
        "port": PORT,
        "reload": DEBUG
    })
    
    uvicorn.run(
        "app:app",
        host=HOST,
        port=PORT,
        reload=DEBUG
    )
