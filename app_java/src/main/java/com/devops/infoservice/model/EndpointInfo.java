package com.devops.infoservice.model;

import lombok.Builder;
import lombok.Data;

/**
 * Endpoint information model
 */
@Data
@Builder
public class EndpointInfo {
    private String path;
    private String method;
    private String description;
}
