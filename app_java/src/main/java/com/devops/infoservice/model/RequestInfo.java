package com.devops.infoservice.model;

import lombok.Builder;
import lombok.Data;

/**
 * Request information model
 */
@Data
@Builder
public class RequestInfo {
    private String clientIp;
    private String userAgent;
    private String method;
    private String path;
}
