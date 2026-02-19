# DevOps Info Service (Java/Spring Boot)

A Spring Boot-based web service that provides detailed information about itself and its runtime environment. This is the compiled language implementation of the DevOps Info Service for the course bonus task.

## Overview

This Java implementation provides the same functionality as the Python version using Spring Boot framework. The service exposes RESTful endpoints that return system information, runtime statistics, and health status, demonstrating enterprise-grade Java application development.

## Prerequisites

- **Java 17+** (JDK 17 or higher)
- **Maven 3.6+** (for building and running)
- Internet connection (for downloading dependencies)

## Installation

### 1. Verify Java Installation

```bash
java -version
# Should show Java 17 or higher
```

### 2. Build the Application

```bash
# Navigate to app_java directory
cd app_java

# Build with Maven (downloads dependencies and compiles)
mvn clean package

# Or build without running tests
mvn clean package -DskipTests
```

This will create an executable JAR file in `target/info-service-1.0.0.jar`.

## Running the Application

### Option 1: Using Maven (Development)

```bash
mvn spring-boot:run
```

### Option 2: Using Compiled JAR (Production)

```bash
java -jar target/info-service-1.0.0.jar
```

### Custom Configuration

Use environment variables or command-line arguments:

```bash
# Custom port using environment variable
PORT=9090 java -jar target/info-service-1.0.0.jar

# Custom port using JVM argument
java -jar target/info-service-1.0.0.jar --server.port=9090

# Custom host and port
HOST=127.0.0.1 PORT=3000 java -jar target/info-service-1.0.0.jar
```

### Access the Application

Once running, access the service at:
- **Main endpoint**: http://localhost:8080/
- **Health check**: http://localhost:8080/health
- **Actuator health**: http://localhost:8080/actuator/health

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
    "framework": "Spring Boot"
  },
  "system": {
    "hostname": "LAPTOP-ABC123",
    "platform": "Windows 11",
    "platformVersion": "10.0",
    "architecture": "amd64",
    "cpuCount": 16,
    "javaVersion": "17.0.8"
  },
  "runtime": {
    "uptimeSeconds": 3600,
    "uptimeHuman": "1 hours, 0 minutes",
    "currentTime": "2026-01-28T14:30:00.000000+00:00",
    "timezone": "UTC"
  },
  "request": {
    "clientIp": "127.0.0.1",
    "userAgent": "Mozilla/5.0...",
    "method": "GET",
    "path": "/"
  },
  "endpoints": [
    {"path": "/", "method": "GET", "description": "Service information"},
    {"path": "/health", "method": "GET", "description": "Health check"}
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
  "uptimeSeconds": 3600
}
```

**Status Code:** 200 OK (when healthy)

## Configuration

The application supports the following configuration options (via environment variables or `application.properties`):

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` / `server.address` | `0.0.0.0` | Host address to bind the server |
| `PORT` / `server.port` | `8080` | Port number to listen on |
| `spring.application.name` | `devops-info-service` | Application name |
| `application.version` | `1.0.0` | Application version |

## Technology Stack

- **Framework**: Spring Boot 3.2.1
- **Language**: Java 17
- **Build Tool**: Maven 3.x
- **Dependencies**:
  - Spring Boot Starter Web (REST API)
  - Spring Boot Starter Actuator (Health checks)
  - Lombok (Reduce boilerplate code)
  - Spring Boot Starter Test (Unit testing)

## Project Structure

```
app_java/
├── pom.xml                                   # Maven configuration
├── .gitignore                                # Git ignore rules
├── README.md                                 # This file
├── src/
│   └── main/
│       ├── java/com/devops/infoservice/
│       │   ├── InfoServiceApplication.java   # Main application class
│       │   ├── controller/
│       │   │   └── InfoController.java       # REST endpoints
│       │   └── model/
│       │       ├── ServiceResponse.java      # Main response model
│       │       ├── ServiceInfo.java          # Service info model
│       │       ├── SystemInfo.java           # System info model
│       │       ├── RuntimeInfo.java          # Runtime info model
│       │       ├── RequestInfo.java          # Request info model
│       │       ├── EndpointInfo.java         # Endpoint info model
│       │       └── HealthResponse.java       # Health response model
│       └── resources/
│           └── application.properties        # Application configuration
└── docs/
    ├── JAVA.md                               # Language justification
    └── LAB01.md                              # Implementation details
```

## Build Information

### Compilation

```bash
# Compile only
mvn compile

# Package into JAR
mvn package

# Clean and rebuild
mvn clean package
```

### Binary Size Comparison

After compilation (`mvn package`), the JAR file size is approximately:
- **Executable JAR (Spring Boot)**: ~20-25 MB (includes embedded Tomcat and all dependencies)
- **Thin JAR (without dependencies)**: ~50 KB (application code only)

Compare this to Python:
- Python application: ~5 KB (source code)
- Python + dependencies: ~50-100 MB (with virtual environment)

The Spring Boot JAR is self-contained and requires only Java runtime to run, making deployment simpler.

## Development

### Spring Boot Features

This application leverages Spring Boot's key features:
- **Auto-configuration**: Minimal configuration required
- **Embedded server**: No external Tomcat/Jetty needed
- **Production-ready**: Built-in health checks and metrics
- **Type safety**: Strong typing with Java
- **Dependency injection**: Clean, testable code architecture

### Code Quality

The codebase follows:
- Java naming conventions
- Clean architecture (Controller → Service → Model)
- Lombok for reducing boilerplate
- Comprehensive Javadoc comments
- RESTful API design principles

### Testing

Run tests with Maven:

```bash
# Run all tests
mvn test

# Run with coverage
mvn test jacoco:report
```

## Comparison with Python Version

| Aspect | Python (FastAPI) | Java (Spring Boot) |
|--------|------------------|-------------------|
| **Startup Time** | ~1 second | ~3-5 seconds |
| **Memory Usage** | ~50-100 MB | ~200-300 MB |
| **Binary Size** | N/A (interpreted) | ~20-25 MB (JAR) |
| **Type Safety** | Optional (hints) | Enforced (compiler) |
| **Performance** | Good (async) | Excellent (JVM) |
| **Ecosystem** | Growing | Mature |
| **Deployment** | Requires Python runtime | Self-contained JAR |
| **Enterprise Adoption** | Increasing | Industry standard |

## Next Steps

This service will be used in future labs for:
- Multi-stage Docker builds (Lab 2)
- Performance comparison with Python version
- Kubernetes deployment with multiple languages
- Demonstrating polyglot microservices architecture

## License

Educational project for DevOps course.

## Docker Support

### Build the Image
Uses multi-stage build:
```bash
# From app_java directory
docker build -t devops-info-service-java .
```

### Run the Container
```bash
docker run -p 8080:8080 devops-info-service-java
```
