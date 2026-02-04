# ==========================================
# Stage 1: Builder
# ==========================================
# Use Maven image with JDK 17 to build the application
FROM maven:3.9-eclipse-temurin-17 AS builder

WORKDIR /build

# Copy only the pom.xml first to verify dependencies and leverage caching
COPY pom.xml .

# Download dependencies (this layer will be cached if pom.xml doesn't change)
RUN mvn dependency:go-offline

# Copy the source code
COPY src ./src

# Build the application (skipping tests for speed in this context)
RUN mvn package -DskipTests

# ==========================================
# Stage 2: Runtime
# ==========================================
# Use a smaller JRE image for running the application
FROM eclipse-temurin:17-jre-alpine

# Set working directory
WORKDIR /app

# Create a non-root user and group
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

# Copy the built JAR file from the builder stage
# The jar name depends on the pom.xml configuration, assuming standard naming
COPY --from=builder /build/target/info-service-1.0.0.jar app.jar

# Change ownership to the non-root user
RUN chown appuser:appgroup app.jar

# Switch to non-root user
USER appuser

# Expose the application port
EXPOSE 8080

# Configure JVM memory settings and run the app
ENTRYPOINT ["java", "-jar", "app.jar"]
