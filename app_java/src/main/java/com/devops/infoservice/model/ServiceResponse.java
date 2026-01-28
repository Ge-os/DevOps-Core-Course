package com.devops.infoservice.model;

import lombok.Builder;
import lombok.Data;

import java.util.List;

/**
 * Main response model for the service information endpoint
 */
@Data
@Builder
public class ServiceResponse {
    private ServiceInfo service;
    private SystemInfo system;
    private RuntimeInfo runtime;
    private RequestInfo request;
    private List<EndpointInfo> endpoints;
}
