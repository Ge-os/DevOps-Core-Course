package com.devops.infoservice.model;

import lombok.Builder;
import lombok.Data;

/**
 * Service information model
 */
@Data
@Builder
public class ServiceInfo {
    private String name;
    private String version;
    private String description;
    private String framework;
}
