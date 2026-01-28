package com.devops.infoservice.controller;

import com.devops.infoservice.model.*;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.lang.management.ManagementFactory;
import java.net.InetAddress;
import java.net.UnknownHostException;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.util.List;

/**
 * Main controller for DevOps Info Service endpoints
 */
@RestController
public class InfoController {

    private static final Instant START_TIME = Instant.now();
    
    @Value("${spring.application.name:devops-info-service}")
    private String applicationName;
    
    @Value("${application.version:1.0.0}")
    private String applicationVersion;

    /**
     * Main endpoint returning comprehensive service and system information
     */
    @GetMapping("/")
    public ServiceResponse getServiceInfo(HttpServletRequest request) {
        return ServiceResponse.builder()
                .service(getServiceInfo())
                .system(getSystemInfo())
                .runtime(getRuntimeInfo())
                .request(getRequestInfo(request))
                .endpoints(getEndpoints())
                .build();
    }

    /**
     * Health check endpoint for monitoring and Kubernetes probes
     */
    @GetMapping("/health")
    public HealthResponse getHealth() {
        long uptimeSeconds = Duration.between(START_TIME, Instant.now()).getSeconds();
        
        return HealthResponse.builder()
                .status("healthy")
                .timestamp(ZonedDateTime.now(ZoneId.of("UTC")).format(DateTimeFormatter.ISO_OFFSET_DATE_TIME))
                .uptimeSeconds(uptimeSeconds)
                .build();
    }

    private ServiceInfo getServiceInfo() {
        return ServiceInfo.builder()
                .name(applicationName)
                .version(applicationVersion)
                .description("DevOps course info service")
                .framework("Spring Boot")
                .build();
    }

    private SystemInfo getSystemInfo() {
        String hostname;
        try {
            hostname = InetAddress.getLocalHost().getHostName();
        } catch (UnknownHostException e) {
            hostname = "unknown";
        }

        return SystemInfo.builder()
                .hostname(hostname)
                .platform(System.getProperty("os.name"))
                .platformVersion(System.getProperty("os.version"))
                .architecture(System.getProperty("os.arch"))
                .cpuCount(Runtime.getRuntime().availableProcessors())
                .javaVersion(System.getProperty("java.version"))
                .build();
    }

    private RuntimeInfo getRuntimeInfo() {
        Duration uptime = Duration.between(START_TIME, Instant.now());
        long uptimeSeconds = uptime.getSeconds();
        long hours = uptimeSeconds / 3600;
        long minutes = (uptimeSeconds % 3600) / 60;

        return RuntimeInfo.builder()
                .uptimeSeconds(uptimeSeconds)
                .uptimeHuman(String.format("%d hours, %d minutes", hours, minutes))
                .currentTime(ZonedDateTime.now(ZoneId.of("UTC")).format(DateTimeFormatter.ISO_OFFSET_DATE_TIME))
                .timezone("UTC")
                .build();
    }

    private RequestInfo getRequestInfo(HttpServletRequest request) {
        String clientIp = request.getRemoteAddr();
        String userAgent = request.getHeader("User-Agent");
        
        return RequestInfo.builder()
                .clientIp(clientIp != null ? clientIp : "unknown")
                .userAgent(userAgent != null ? userAgent : "unknown")
                .method(request.getMethod())
                .path(request.getRequestURI())
                .build();
    }

    private List<EndpointInfo> getEndpoints() {
        return List.of(
                EndpointInfo.builder()
                        .path("/")
                        .method("GET")
                        .description("Service information")
                        .build(),
                EndpointInfo.builder()
                        .path("/health")
                        .method("GET")
                        .description("Health check")
                        .build()
        );
    }
}
