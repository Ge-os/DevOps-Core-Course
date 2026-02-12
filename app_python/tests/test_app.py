"""
Unit tests for the DevOps Info Service application.
Tests all endpoints with comprehensive coverage.
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime
import platform
import socket

from app import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)


class TestRootEndpoint:
    """Tests for the main / endpoint."""
    
    def test_root_status_code(self, client):
        """Test that root endpoint returns 200 OK."""
        response = client.get("/")
        assert response.status_code == 200
    
    def test_root_returns_json(self, client):
        """Test that root endpoint returns JSON content."""
        response = client.get("/")
        assert response.headers["content-type"] == "application/json"
    
    def test_root_has_required_sections(self, client):
        """Test that response contains all required top-level sections."""
        response = client.get("/")
        data = response.json()
        
        assert "service" in data
        assert "system" in data
        assert "runtime" in data
        assert "request" in data
        assert "endpoints" in data
    
    def test_service_info_structure(self, client):
        """Test that service section has correct structure and values."""
        response = client.get("/")
        data = response.json()
        service = data["service"]
        
        assert service["name"] == "devops-info-service"
        assert service["version"] == "1.0.0"
        assert service["description"] == "DevOps course info service"
        assert service["framework"] == "FastAPI"
    
    def test_system_info_structure(self, client):
        """Test that system section contains all required fields."""
        response = client.get("/")
        data = response.json()
        system = data["system"]
        
        required_fields = [
            "hostname", "platform", "platform_version",
            "architecture", "cpu_count", "python_version"
        ]
        for field in required_fields:
            assert field in system
            assert system[field] is not None
    
    def test_system_info_values(self, client):
        """Test that system info returns valid data types."""
        response = client.get("/")
        data = response.json()
        system = data["system"]
        
        # Check data types
        assert isinstance(system["hostname"], str)
        assert isinstance(system["platform"], str)
        assert isinstance(system["architecture"], str)
        assert isinstance(system["cpu_count"], int)
        assert isinstance(system["python_version"], str)
        
        # Check that values are not empty
        assert len(system["hostname"]) > 0
        assert system["cpu_count"] > 0
    
    def test_runtime_info_structure(self, client):
        """Test that runtime section contains all required fields."""
        response = client.get("/")
        data = response.json()
        runtime = data["runtime"]
        
        required_fields = [
            "uptime_seconds", "uptime_human", 
            "current_time", "timezone"
        ]
        for field in required_fields:
            assert field in runtime
    
    def test_runtime_uptime_values(self, client):
        """Test that uptime values are valid."""
        response = client.get("/")
        data = response.json()
        runtime = data["runtime"]
        
        # Uptime should be non-negative integer
        assert isinstance(runtime["uptime_seconds"], int)
        assert runtime["uptime_seconds"] >= 0
        
        # Human readable uptime should contain hours and minutes
        assert "hours" in runtime["uptime_human"]
        assert "minutes" in runtime["uptime_human"]
        
        # Timezone should be UTC
        assert runtime["timezone"] == "UTC"
    
    def test_runtime_current_time_format(self, client):
        """Test that current_time is in ISO format."""
        response = client.get("/")
        data = response.json()
        
        # Should be able to parse as ISO datetime
        current_time_str = data["runtime"]["current_time"]
        parsed_time = datetime.fromisoformat(current_time_str.replace('Z', '+00:00'))
        assert parsed_time is not None
    
    def test_request_info_structure(self, client):
        """Test that request section contains all required fields."""
        response = client.get("/")
        data = response.json()
        request = data["request"]
        
        required_fields = ["client_ip", "user_agent", "method", "path"]
        for field in required_fields:
            assert field in request
    
    def test_request_info_values(self, client):
        """Test that request info contains correct values."""
        response = client.get("/")
        data = response.json()
        request = data["request"]
        
        # Method should be GET
        assert request["method"] == "GET"
        
        # Path should be /
        assert request["path"] == "/"
        
        # Client IP should be present (testclient uses testclient)
        assert request["client_ip"] is not None
        
        # User agent should be present
        assert request["user_agent"] is not None
    
    def test_request_custom_user_agent(self, client):
        """Test that custom user agent is captured correctly."""
        custom_ua = "CustomBot/1.0"
        response = client.get("/", headers={"user-agent": custom_ua})
        data = response.json()
        
        assert data["request"]["user_agent"] == custom_ua
    
    def test_endpoints_list_structure(self, client):
        """Test that endpoints list is present and has correct structure."""
        response = client.get("/")
        data = response.json()
        endpoints = data["endpoints"]
        
        # Should be a list
        assert isinstance(endpoints, list)
        
        # Should have at least 2 endpoints
        assert len(endpoints) >= 2
        
        # Each endpoint should have required fields
        for endpoint in endpoints:
            assert "path" in endpoint
            assert "method" in endpoint
            assert "description" in endpoint
    
    def test_endpoints_list_content(self, client):
        """Test that endpoints list contains expected endpoints."""
        response = client.get("/")
        data = response.json()
        endpoints = data["endpoints"]
        
        # Get paths from endpoints
        paths = [ep["path"] for ep in endpoints]
        
        # Should include / and /health
        assert "/" in paths
        assert "/health" in paths


class TestHealthEndpoint:
    """Tests for the /health endpoint."""
    
    def test_health_status_code(self, client):
        """Test that health endpoint returns 200 OK."""
        response = client.get("/health")
        assert response.status_code == 200
    
    def test_health_returns_json(self, client):
        """Test that health endpoint returns JSON content."""
        response = client.get("/health")
        assert response.headers["content-type"] == "application/json"
    
    def test_health_response_structure(self, client):
        """Test that health response contains all required fields."""
        response = client.get("/health")
        data = response.json()
        
        required_fields = ["status", "timestamp", "uptime_seconds"]
        for field in required_fields:
            assert field in data
    
    def test_health_status_value(self, client):
        """Test that status is 'healthy'."""
        response = client.get("/health")
        data = response.json()
        
        assert data["status"] == "healthy"
    
    def test_health_timestamp_format(self, client):
        """Test that timestamp is in ISO format."""
        response = client.get("/health")
        data = response.json()
        
        # Should be able to parse as ISO datetime
        timestamp_str = data["timestamp"]
        parsed_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        assert parsed_time is not None
    
    def test_health_uptime_value(self, client):
        """Test that uptime is a valid non-negative integer."""
        response = client.get("/health")
        data = response.json()
        
        assert isinstance(data["uptime_seconds"], int)
        assert data["uptime_seconds"] >= 0
    
    def test_health_uptime_increases(self, client):
        """Test that uptime increases between calls."""
        import time
        
        response1 = client.get("/health")
        uptime1 = response1.json()["uptime_seconds"]
        
        # Wait a bit
        time.sleep(0.1)
        
        response2 = client.get("/health")
        uptime2 = response2.json()["uptime_seconds"]
        
        # Uptime should be same or increased (might be same if very fast)
        assert uptime2 >= uptime1


class TestErrorHandling:
    """Tests for error scenarios and edge cases."""
    
    def test_nonexistent_endpoint(self, client):
        """Test that non-existent endpoints return 404."""
        response = client.get("/nonexistent")
        assert response.status_code == 404
    
    def test_post_to_get_only_endpoint(self, client):
        """Test that POST to GET-only endpoint returns 405."""
        response = client.post("/")
        assert response.status_code == 405
    
    def test_post_to_health_endpoint(self, client):
        """Test that POST to health endpoint returns 405."""
        response = client.post("/health")
        assert response.status_code == 405


class TestResponseConsistency:
    """Tests for response consistency across multiple calls."""
    
    def test_multiple_root_calls_consistency(self, client):
        """Test that multiple calls to root return consistent structure."""
        response1 = client.get("/")
        response2 = client.get("/")
        
        data1 = response1.json()
        data2 = response2.json()
        
        # Structure should be identical
        assert data1.keys() == data2.keys()
        assert data1["service"] == data2["service"]
        assert data1["system"] == data2["system"]
        # Runtime values will differ (time, uptime) but structure should match
        assert data1["runtime"].keys() == data2["runtime"].keys()
    
    def test_multiple_health_calls_consistency(self, client):
        """Test that multiple calls to health return consistent structure."""
        response1 = client.get("/health")
        response2 = client.get("/health")
        
        data1 = response1.json()
        data2 = response2.json()
        
        # Structure should be identical
        assert data1.keys() == data2.keys()
        # Status should always be healthy
        assert data1["status"] == "healthy"
        assert data2["status"] == "healthy"
