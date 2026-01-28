"""
DevOps Info Service
Main application module using FastAPI framework
"""
import os
import socket
import platform
from datetime import datetime, timezone
from typing import Dict, Any

from fastapi import FastAPI, Request

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


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app:app",
        host=HOST,
        port=PORT,
        reload=DEBUG
    )
