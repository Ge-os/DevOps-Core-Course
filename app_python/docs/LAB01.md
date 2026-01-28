# Lab 01 - DevOps Info Service: Web Application Development

**Student**: Selivanov George  
**Date**: January 28, 2026  
**Framework**: FastAPI 0.115.0  

## Task 1 - Python Web Application (6 pts)

### 1.1 Project Structure 

Created the following project structure:

```
app_python/
├── app.py                    # Main FastAPI application
├── requirements.txt         # All dependencies
├── .gitignore               # Git ignore rules
├── README.md                # User-facing documentation
├── tests/                   # Unit tests (Lab 3)
│   └── __init__.py
└── docs/                    # Lab documentation
    ├── LAB01.md            # This file
    └── screenshots/        # Proof of work
        ├── 01-main-endpoint.png
        ├── 02-health-check.png
        └── 03-formatted-output.png
```

### 1.2 Web Framework Choice 

**Selected Framework**: FastAPI 0.115.0

**Justification**:
- **Modern & Fast**: Built on Starlette and Pydantic, offering excellent performance
- **Async Support**: Native async/await support for handling concurrent requests efficiently
- **Automatic Documentation**: Auto-generates interactive API docs (Swagger UI and ReDoc)
- **Type Safety**: Leverages Python type hints for validation and IDE support
- **Industry Standard**: Widely adopted for microservices and REST APIs
- **Future-Ready**: Perfect foundation for containerization and Kubernetes deployment

While Flask is simpler for beginners, FastAPI's built-in features (validation, docs, async) provide better value for a DevOps service that will scale throughout the course.

### 1.3 Main Endpoint Implementation 

Implemented `GET /` endpoint that returns:

**Features**:
- Service information (name, version, description, framework)
- System information (hostname, platform, architecture, CPU count, Python version)
- Runtime statistics (uptime in seconds and human-readable format, current time, timezone)
- Request details (client IP, user agent, HTTP method, path)
- Available endpoints list

**Code Location**: [app.py](../app.py)

The endpoint uses:
- `socket.gethostname()` for hostname
- `platform` module for system information
- `datetime` for uptime calculation and timestamps
- `Request` object for client information

### 1.4 Health Check Endpoint 

Implemented `GET /health` endpoint:

**Features**:
- Returns HTTP 200 status
- Simple JSON response with status, timestamp, and uptime
- Designed for Kubernetes liveness/readiness probes

**Response Format**:
```json
{
  "status": "healthy",
  "timestamp": "2026-01-28T19:47:18.526182+00:00",
  "uptime_seconds": 221690
}
```

### 1.5 Configuration 

Implemented environment variable configuration:

**Supported Variables**:
- `HOST` - Server bind address (default: 0.0.0.0)
- `PORT` - Server port (default: 5000)
- `DEBUG` - Enable debug/reload mode (default: False)

**Usage Examples**:
```bash
python app.py                    # Default: 0.0.0.0:5000
PORT=8080 python app.py          # Custom port
HOST=127.0.0.1 PORT=3000 python app.py  # Custom host and port
DEBUG=true python app.py         # Enable auto-reload
```

## Task 2 - Documentation & Best Practices (4 pts)

### 2.1 Application README 

Created comprehensive [README.md](../README.md) with:

1. **Overview** - Service description and purpose
2. **Prerequisites** - Python version requirements
3. **Installation** - Virtual environment setup and dependency installation
4. **Running the Application** - Default and custom configurations
5. **API Endpoints** - Detailed endpoint documentation with examples
6. **Configuration** - Environment variables table
7. **Technology Stack** - Framework and dependencies
8. **Project Structure** - Directory layout
9. **Development** - FastAPI features and code quality notes
10. **Next Steps** - Future lab enhancements

### 2.2 Best Practices 

**Implemented Best Practices**:

1. **Clean Code Organization**:
   - Proper imports grouping (standard library, third-party, local)
   - Clear function names (`get_uptime()`, `get_system_info()`)
   - Comprehensive docstrings for all functions and endpoints
   - PEP 8 compliant formatting

2. **Type Hints**:
   - All functions have type annotations
   - Return types specified (`Dict[str, Any]`)
   - Leverages FastAPI's automatic validation

3. **Configuration Management**:
   - Environment variables for configuration
   - Sensible defaults
   - Centralized configuration at module level

4. **Error Handling**:
   - FastAPI handles validation errors automatically
   - Safe fallbacks (e.g., `request.client.host if request.client else "unknown"`)

5. **Documentation**:
   - Module-level docstring
   - Function docstrings with descriptions
   - Inline comments where logic needs clarification

## Dependencies

### requirements.txt (All Installed Packages)
All dependencies with exact versions captured via `pip freeze`:
- FastAPI and its dependencies (Starlette, Pydantic)
- Uvicorn with standard extras (watchfiles, websockets, httptools, etc.)
- Supporting libraries (click, colorama, PyYAML, python-dotenv)

See [requirements.txt](../requirements.txt) for complete list.

## Testing

### Running the Application

1. **Activate virtual environment**:
   ```bash
   .venv\Scripts\activate  # Windows
   ```

2. **Start the server**:
   ```bash
   python app.py
   ```

3. **Access endpoints**:
   - Main endpoint: http://localhost:5000/
   - Health check: http://localhost:5000/health
   - Interactive docs: http://localhost:5000/docs

### Expected Behavior

- **Main endpoint** returns complete JSON with service, system, runtime, and request info
- **Health endpoint** returns simple status JSON
- **Server logs** show INFO messages from Uvicorn
- **Auto-documentation** accessible at `/docs` and `/redoc`

## Screenshots

Screenshots demonstrating the working application should be placed in:
- `docs/screenshots/01-main-endpoint.png`
- `docs/screenshots/02-health-check.png`
- `docs/screenshots/03-formatted-output.png`

## Conclusion

Successfully implemented a FastAPI-based DevOps info service with:
- Complete project structure
- Two functional endpoints (`/` and `/health`)
- Environment-based configuration
- Comprehensive documentation
- Best practices and code quality
- Virtual environment with `.venv`
- Dependencies managed with requirements.txt
- Full dependency snapshot with pip freeze

The application is ready for future enhancements including testing, containerization, and deployment automation.
