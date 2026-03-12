"""
DevOps Info Service
Main application module using FastAPI framework
"""
import os
import sys
import socket
import platform
import logging
import json
from datetime import datetime, timezone
from typing import Dict, Any

from fastapi import FastAPI, Request
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
    # Log incoming request
    logger.info("HTTP Request", extra={
        "method": request.method,
        "path": request.url.path,
        "client_ip": request.client.host if request.client else "unknown",
        "user_agent": request.headers.get('user-agent', 'unknown')
    })
    
    # Process request
    response = await call_next(request)
    
    # Log response
    logger.info("HTTP Response", extra={
        "method": request.method,
        "path": request.url.path,
        "status_code": response.status_code
    })
    
    return response


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


@app.get("/")
async def root(request: Request) -> Dict[str, Any]:
    """
    Main endpoint returning comprehensive service and system information.
    
    Returns:
        Dict containing service, system, runtime, request info and available endpoints
    """
    uptime = get_uptime()
    system_info = get_system_info()
    
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
            "timezone": "UTC"
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
    uptime = get_uptime()
    
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": uptime['seconds']
    }


# Startup event
@app.on_event("startup")
async def startup_event():
    """Log application startup"""
    logger.info("Application started successfully", extra={
        "service": "devops-info-service",
        "version": "1.0.0",
        "startup_time": start_time.isoformat()
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
