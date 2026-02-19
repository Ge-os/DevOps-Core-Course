# Lab 01 Bonus - Java/Spring Boot Implementation

**Language**: Java 17  
**Framework**: Spring Boot 3.2.1  
**Date**: January 28, 2026  

## Implementation Overview

This is the compiled language bonus implementation of the DevOps Info Service using Java and Spring Boot. It provides identical functionality to the Python/FastAPI version while demonstrating enterprise-grade Java application development.

## Language & Framework Selection

**Selected**: Java 17 with Spring Boot 3.2.1

See [JAVA.md](JAVA.md) for detailed justification covering:
- Compiled language benefits (type safety, performance, binary distribution)
- Enterprise adoption and industry standards
- Spring Boot's production-ready features
- Cloud-native architecture support
- Comparison with Go, Rust, and C#/.NET alternatives

**Key Advantages for DevOps Course:**
- Multi-stage Docker build demonstration
- Polyglot microservices architecture example
- Enterprise development best practices
- Performance comparison baseline

## Project Structure

```
app_java/
├── pom.xml                                        # Maven configuration
├── .gitignore                                     # Git ignore rules
├── README.md                                      # User documentation
├── src/
│   └── main/
│       ├── java/com/devops/infoservice/
│       │   ├── InfoServiceApplication.java        # Main Spring Boot application
│       │   ├── controller/
│       │   │   └── InfoController.java            # REST API endpoints
│       │   └── model/
│       │       ├── ServiceResponse.java           # Main response DTO
│       │       ├── ServiceInfo.java               # Service info DTO
│       │       ├── SystemInfo.java                # System info DTO
│       │       ├── RuntimeInfo.java               # Runtime info DTO
│       │       ├── RequestInfo.java               # Request info DTO
│       │       ├── EndpointInfo.java              # Endpoint info DTO
│       │       └── HealthResponse.java            # Health response DTO
│       └── resources/
│           └── application.properties             # Application configuration
└── docs/
    ├── JAVA.md                                    # Language justification (this file)
    └── LAB01.md                                   # Implementation documentation
```

## Implementation Details

### 1. Main Endpoint: `GET /`

**Location**: [InfoController.java](../src/main/java/com/devops/infoservice/controller/InfoController.java)

**Features Implemented:**
- Service information (name, version, description, framework)
- System information (hostname, platform, architecture, CPU count, Java version)
- Runtime statistics (uptime in seconds and human-readable, current time, timezone)
- Request details (client IP, user agent, HTTP method, path)
- Available endpoints list

**Implementation Highlights:**

```java
@GetMapping("/")
public ServiceResponse getServiceInfo(HttpServletRequest request) {
    return ServiceResponse.builder()
            .service(getServiceInfo())
            .system(getSystemInfo())
            .runtime(getRuntimeInfo())
            .request(getRequestInfo(request))
            .endpoints(getEndpoints())
            .build();
}
```

**System Information Collection:**
- Hostname: `InetAddress.getLocalHost().getHostName()`
- Platform: `System.getProperty("os.name")`
- Architecture: `System.getProperty("os.arch")`
- CPU Count: `Runtime.getRuntime().availableProcessors()`
- Java Version: `System.getProperty("java.version")`

**Uptime Calculation:**
```java
private static final Instant START_TIME = Instant.now();

Duration uptime = Duration.between(START_TIME, Instant.now());
long uptimeSeconds = uptime.getSeconds();
long hours = uptimeSeconds / 3600;
long minutes = (uptimeSeconds % 3600) / 60;
```

### 2. Health Check Endpoint: `GET /health`

**Location**: Same controller file

**Features Implemented:**
-  Returns HTTP 200 status code
-  Simple JSON response with status, timestamp, and uptime
-  UTC timezone for consistency
-  Kubernetes-ready health probe format

**Implementation:**

```java
@GetMapping("/health")
public HealthResponse getHealth() {
    long uptimeSeconds = Duration.between(START_TIME, Instant.now()).getSeconds();
    
    return HealthResponse.builder()
            .status("healthy")
            .timestamp(ZonedDateTime.now(ZoneId.of("UTC"))
                      .format(DateTimeFormatter.ISO_OFFSET_DATE_TIME))
            .uptimeSeconds(uptimeSeconds)
            .build();
}
```

### 3. Configuration Management

**Location**: [application.properties](../src/main/resources/application.properties)

**Environment Variables Supported:**
```properties
server.port=${PORT:8080}          # Default: 8080
server.address=${HOST:0.0.0.0}    # Default: 0.0.0.0
```

**Testing Configuration:**
```bash
# Default (port 8080)
java -jar target/info-service-1.0.0.jar

# Custom port
PORT=9090 java -jar target/info-service-1.0.0.jar

# Custom host and port
HOST=127.0.0.1 PORT=3000 java -jar target/info-service-1.0.0.jar
```

### 4. Model Classes

**Design Pattern**: Data Transfer Objects (DTOs) with Lombok builders

**Benefits:**
- Immutable data structures
- Type-safe JSON serialization
- Clean, readable code (no boilerplate)
- Builder pattern for flexible construction

**Example:**
```java
@Data
@Builder
public class SystemInfo {
    private String hostname;
    private String platform;
    private String platformVersion;
    private String architecture;
    private Integer cpuCount;
    private String javaVersion;
}
```

## Best Practices Implemented

### 1. Clean Architecture

**Separation of Concerns:**
- `controller/` - HTTP request handling
- `model/` - Data structures and DTOs
- `resources/` - Configuration files

**Benefits:**
- Easy to test each layer independently
- Clear responsibility boundaries
- Scalable for future features

### 2. Type Safety

**Compile-Time Checking:**
```java
// This won't compile - type mismatch caught early
SystemInfo info = SystemInfo.builder()
    .cpuCount("8")  // Compiler error: String cannot be converted to Integer
    .build();
```

**Comparison with Python:**
- Python: Type hints are optional and not enforced
- Java: All types are checked at compile time
- Prevents entire classes of runtime errors

### 3. Dependency Management

**Maven POM ([pom.xml](../pom.xml)):**

```xml
<dependencies>
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-web</artifactId>
    </dependency>
    <!-- Other dependencies -->
</dependencies>
```

**Benefits:**
- Transitive dependency resolution
- Version management via parent POM
- Reproducible builds
- Central repository (Maven Central)

### 4. Production-Ready Features

**Spring Boot Actuator:**
- Health check endpoint (`/actuator/health`)
- Application info endpoint
- Metrics collection ready
- Production monitoring integration

**Logging:**
```properties
logging.level.root=INFO
logging.level.com.devops.infoservice=DEBUG
logging.pattern.console=%d{yyyy-MM-dd HH:mm:ss} - %logger{36} - %msg%n
```

### 5. Documentation

**Javadoc Comments:**
```java
/**
 * Main endpoint returning comprehensive service and system information
 * 
 * @param request HTTP servlet request for extracting client information
 * @return ServiceResponse containing all service and system details
 */
@GetMapping("/")
public ServiceResponse getServiceInfo(HttpServletRequest request) {
    // Implementation
}
```

## Build Process

### Compilation Steps

```bash
# 1. Clean previous builds
mvn clean

# 2. Compile source code
mvn compile

# 3. Run tests (if any)
mvn test

# 4. Package into JAR
mvn package

# Output: target/info-service-1.0.0.jar
```

### Build Output

**Generated Artifacts:**
- `info-service-1.0.0.jar` - Executable fat JAR (~20-25 MB)
- Includes all dependencies and embedded Tomcat server
- Self-contained, only requires Java runtime to execute

## Binary Size Comparison

### Java (Spring Boot)
```bash
# After mvn package
ls -lh target/info-service-1.0.0.jar
# ~20-25 MB (fat JAR with all dependencies)
```

### Python (FastAPI)
```bash
# Source code only
du -sh app_python/app.py
# ~5 KB (source code)

# With virtual environment
du -sh app_python/.venv
# ~50-100 MB (Python runtime + dependencies)
```

### Comparison Table

| Metric | Python (FastAPI) | Java (Spring Boot) |
|--------|------------------|-------------------|
| **Source Code** | ~5 KB | ~15 KB |
| **Dependencies Size** | ~50-100 MB (venv) | Included in JAR |
| **Distribution Size** | N/A (interpreted) | ~20-25 MB (JAR) |
| **Runtime Required** | Python 3.11+ | Java 17+ |
| **Startup Time** | ~1 second | ~3-5 seconds |
| **Memory Usage** | ~50-100 MB | ~200-300 MB |
| **Distribution** | Source + venv | Single JAR file |

**Key Differences:**
- **Java**: Single self-contained JAR, consistent across environments
- **Python**: Requires Python runtime and virtual environment setup
- **Java**: Larger initial footprint but includes everything needed
- **Python**: Smaller code but larger total deployment with dependencies

## Testing the Application

### 1. Build the Application

```bash
cd app_java
mvn clean package
```

### 2. Run the Application

```bash
java -jar target/info-service-1.0.0.jar
```

### 3. Test Endpoints

**Main Endpoint:**
```bash
curl http://localhost:8080/

# Or in PowerShell
Invoke-WebRequest -Uri http://localhost:8080/ | Select-Object -ExpandProperty Content
```

**Expected Response:**
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
    "uptimeSeconds": 45,
    "uptimeHuman": "0 hours, 0 minutes",
    "currentTime": "2026-01-28T19:30:00.000000+00:00",
    "timezone": "UTC"
  },
  "request": {
    "clientIp": "127.0.0.1",
    "userAgent": "curl/8.0.1",
    "method": "GET",
    "path": "/"
  },
  "endpoints": [
    {"path": "/", "method": "GET", "description": "Service information"},
    {"path": "/health", "method": "GET", "description": "Health check"}
  ]
}
```

**Health Check:**
```bash
curl http://localhost:8080/health

# Expected Response:
# {
#   "status": "healthy",
#   "timestamp": "2026-01-28T19:30:00.000000+00:00",
#   "uptimeSeconds": 120
# }
```

## Challenges & Solutions

### Challenge 1: JAR Size

**Problem**: Spring Boot fat JAR is ~20 MB, much larger than Python source

**Solution**: This is intentional and beneficial:
- Single file deployment (no dependency installation needed)
- Includes embedded server (no external Tomcat)
- Consistent across all environments
- Will demonstrate multi-stage Docker builds in Lab 2

### Challenge 2: Startup Time

**Problem**: JVM startup takes 3-5 seconds vs Python's 1 second

**Solution**: Acceptable trade-off for production benefits:
- Better runtime performance after startup
- More predictable behavior under load
- Can be optimized with GraalVM native images (future)
- Not significant for long-running services

### Challenge 3: Memory Footprint

**Problem**: Java uses more memory (~200 MB) than Python (~50 MB)

**Solution**: Memory is cheap, reliability is expensive:
- More thorough error checking
- Better garbage collection
- Production monitoring built-in
- Predictable memory patterns

## Advantages Over Python Version

### 1. Type Safety
- Compile-time error detection
- Refactoring confidence
- Better IDE support

### 2. Production Features
- Built-in health checks (Actuator)
- Metrics and monitoring ready
- Mature observability ecosystem

### 3. Single-File Deployment
- JAR contains everything needed
- No virtual environment setup
- Version conflicts impossible

### 4. Enterprise Support
- Long-term support (LTS) versions
- Professional tooling
- Corporate backing

### 5. Performance at Scale
- Better multi-threading
- Efficient resource usage
- Proven in high-load scenarios

## Conclusion

The Java/Spring Boot implementation successfully demonstrates:

 **Compiled Language Benefits**: Type safety, single binary distribution  
 **Same Functionality**: Identical JSON structure and endpoints as Python version  
 **Enterprise Readiness**: Production-ready features and best practices  
 **Clean Architecture**: Well-structured, maintainable code  
 **Configuration Management**: Environment variable support  
 **Build Process**: Maven-based, reproducible builds  
 **Documentation**: Comprehensive README and code comments  

This implementation provides an excellent foundation for:
- Multi-stage Docker builds (Lab 2)
- Kubernetes deployments with different languages
- Performance comparison studies
- Polyglot microservices architecture demonstrations

The Java version complements the Python implementation, showcasing how DevOps practices apply across different technology stacks while highlighting the unique benefits of compiled languages in production environments.
