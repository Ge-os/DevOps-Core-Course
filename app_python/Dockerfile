# Use official Python runtime as a parent image
# Using slim version for smaller image size
FROM python:3.13-slim

# Set the working directory in the container
WORKDIR /app

# Create a non-root user for security
# -u 1001: Run with specific UID
# -m: Create home directory
RUN useradd -u 1001 -m appuser

# Copy requirements file first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
# --no-cache-dir: Don't cache the installed packages to save space
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Change ownership of the application files to the non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Run app.py when the container launches
CMD ["python", "app.py"]
