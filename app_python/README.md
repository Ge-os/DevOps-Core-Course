# DevOps Info Service

A FastAPI-based web service that provides detailed information about itself and its runtime environment. Built as part of the DevOps course, this service will evolve into a comprehensive monitoring tool.

## Overview

The DevOps Info Service exposes RESTful endpoints that return system information, runtime statistics, and health status. This foundation will be extended throughout the course with containerization, CI/CD pipelines, monitoring, and persistence capabilities.

## Prerequisites

- Python 3.11+ 
- pip (Python package installer)
- Virtual environment support

## Installation

1. **Create and activate a virtual environment:**

   ```bash
   # Windows
   python -m venv .venv
   .venv\Scripts\activate

   # Linux/macOS
   python -m venv .venv
   source .venv/bin/activate
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

### Default Configuration

Run the application with default settings (0.0.0.0:5000):

```bash
python app.py
```

### Custom Configuration

Use environment variables to customize the application:

```bash
# Custom port
PORT=8080 python app.py

# Custom host and port
HOST=127.0.0.1 PORT=3000 python app.py

# Enable debug mode (auto-reload on code changes)
DEBUG=true python app.py
```

### Access the Application

Once running, access the service at:
- **Main endpoint**: http://localhost:5000/
- **Health check**: http://localhost:5000/health
- **Interactive API docs**: http://localhost:5000/docs

## API Endpoints

### GET `/`

Returns comprehensive service and system information.

**Response:**
```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "FastAPI"
  },
  "system": {
    "hostname": "LAPTOP-MR94R9P1",
    "platform": "Windows",
    "platform_version": "10.0.26200",
    "architecture": "AMD64",
    "cpu_count": 16,
    "python_version": "3.11.0"
  },
  "runtime": {
    "uptime_seconds": 500,
    "uptime_human": "12 hours, 8 minutes",
    "current_time": "2026-01-28T19:18:42.601851+00:00",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "127.0.0.1",
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
    "method": "GET",
    "path": "/"
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
```

### GET `/health`

Simple health check endpoint for monitoring systems and Kubernetes probes.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-28T14:30:00.000000+00:00",
  "uptime_seconds": 3600
}
```

**Status Code:** 200 OK (when healthy)

## Configuration

The application supports the following environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Host address to bind the server |
| `PORT` | `5000` | Port number to listen on |
| `DEBUG` | `False` | Enable debug mode with auto-reload |

## Technology Stack

- **Framework**: FastAPI 0.115.0
- **ASGI Server**: Uvicorn 0.32.1
- **Language**: Python 3.11.1

## Project Structure

```
app_python/
├── app.py                    # Main application
├── requirements.txt          # All dependencies
├── .gitignore                # Git ignore rules
├── README.md                 # This file
├── tests/                    # Unit tests (Lab 3)
│   └── __init__.py
└── docs/                     # Lab documentation
    └── screenshots/          # Proof of work
        ├── 01-main-endpoint.png
        ├── 02-health-check.png
        └── 03-formatted-output.png
```

## Development

### FastAPI Features

This application leverages FastAPI's key features:
- **Automatic API documentation** (Swagger UI and ReDoc)
- **Type hints and validation** with Pydantic
- **Async/await support** for high performance
- **Standards-based** (OpenAPI, JSON Schema)