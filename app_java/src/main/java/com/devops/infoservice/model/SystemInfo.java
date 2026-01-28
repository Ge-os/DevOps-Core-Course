package com.devops.infoservice.model;

import lombok.Builder;
import lombok.Data;

/**
 * System information model
 */
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
