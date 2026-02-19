package com.devops.infoservice.model;

import lombok.Builder;
import lombok.Data;

/**
 * Health check response model
 */
@Data
@Builder
public class HealthResponse {
    private String status;
    private String timestamp;
    private Long uptimeSeconds;
}
