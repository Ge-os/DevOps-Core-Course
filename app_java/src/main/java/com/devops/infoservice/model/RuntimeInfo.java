package com.devops.infoservice.model;

import lombok.Builder;
import lombok.Data;

/**
 * Runtime information model
 */
@Data
@Builder
public class RuntimeInfo {
    private Long uptimeSeconds;
    private String uptimeHuman;
    private String currentTime;
    private String timezone;
}
