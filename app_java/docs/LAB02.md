# Lab 2 (Bonus): Multi-Stage Build for Java Application

**Student**: Selivanov George
**Date**: February 04, 2026

## 1. Multi-Stage Build Strategy

For the Java application (`app_java`), I implemented a multi-stage build to separate the **build environment** (which requires Maven and the full JDK) from the **execution environment** (which only needs a lightweight JRE).

### Stage 1: Builder (`maven:3.9-eclipse-temurin-17`)
*   **Purpose:** Compile source code and package the JAR file.
*   **Actions:**
    1.  Pre-download Maven dependencies (cached layer).
    2.  Build the application using `mvn package`.
*   **Result:** A `target/` directory containing the compiled artifact.

### Stage 2: Runtime (`eclipse-temurin:17-jre-alpine`)
*   **Purpose:** Run the application in a minimal, secure environment.
*   **Actions:**
    1.  Create a non-root user.
    2.  Copy **only** the compiled JAR from Stage 1.
    3.  Set the entrypoint.

## 2. Size Comparison & Analysis

| Image Type | Base Image | Approx. Size | Content |
|------------|------------|--------------|---------|
| **Builder Image** | `maven:3.9-eclipse-temurin-17` | ~600 MB | Full JDK, Maven, Source Code, Local Maven Repo (`~/.m2`) |
| **Final Image** | `eclipse-temurin:17-jre-alpine` | ~170 MB | Just JRE + Compiled JAR |

**Why Multi-Stage Matters for Compiled Languages:**
In languages like Java or Go, the build tools (javac, maven, go cli) are required to compile the code but are strictly **useless** at runtime. Including them in the final production image:
1.  **Bloats the image:** Wastes disk space and bandwidth.
2.  **Increases Attack Surface:** Compilers and build tools can be exploited by attackers to compile malicious code inside a compromised container.
3.  **Leaks Source Code:** Start-up scripts or cached layers might accidentally leave source code in the image.

By copying only the artifact (`app.jar`), the final image is **clean**, **small**, and **secure**.

## 3. Terminal Output: Build Process

```text
$ docker build -t devops-java-app .
```

## 4. Technical Explanation

### 4.1 Layer Caching (Optimization)
I separated the `pom.xml` copy from the source code copy:
```dockerfile
COPY pom.xml .
RUN mvn dependency:go-offline
COPY src ./src
```
**Reason:** Maven dependencies (internet downloads) take a long time. They only change when `pom.xml` changes. Source code (`src/`) changes frequently. By putting `pom.xml` first, Docker caches the `mvn dependency:go-offline` layer. If I change a Java file and run `docker build` again, it skips the download step entirely, making builds instant.

### 4.2 Security (Non-Root)
I explicitly created a user in the Alpine image:
```dockerfile
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
USER appuser
```
**Reason:** Alpine's default user is root. Running as `appuser` effectively sandboxes the process.

### 4.3 Base Image Selection
I chose `eclipse-temurin:17-jre-alpine`.
*   `eclipse-temurin`: High-performance, production-ready OpenJDK build.
*   `17-jre`: Only the Runtime Environment, not the full JDK.
*   `alpine`: Uses musl libc and BusyBox, resulting in a tiny OS footprint (~5MB base).
