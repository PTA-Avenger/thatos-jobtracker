package com.jobtracker.backend.controllers;

import com.jobtracker.backend.entities.Application;
import com.jobtracker.backend.entities.User;
import com.jobtracker.backend.repositories.ApplicationRepository;
import com.jobtracker.backend.repositories.UserRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/dashboard")
public class DashboardController {

    @Autowired
    private ApplicationRepository applicationRepository;

    @Autowired
    private UserRepository userRepository;

    private User getAuthenticatedUser() {
        String username = SecurityContextHolder.getContext().getAuthentication().getName();
        return userRepository.findByUsername(username)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.UNAUTHORIZED, "User not found"));
    }

    @GetMapping("/stats")
    public ResponseEntity<?> getDashboardStats() {
        User user = getAuthenticatedUser();
        List<Application> applications = applicationRepository.findByUser(user);

        long totalCount = applications.size();

        // 1. Group by status
        Map<String, Long> statusCounts = applications.stream()
                .collect(Collectors.groupingBy(Application::getStatus, Collectors.counting()));

        // Ensure all standard statuses are present in the map
        String[] standardStatuses = {"Saved", "Applied", "Interview", "Offer", "Rejected"};
        for (String status : standardStatuses) {
            statusCounts.putIfAbsent(status, 0L);
        }

        // 2. Group by date applied (activity over time)
        Map<String, Long> timelineCounts = new HashMap<>();
        for (Application app : applications) {
            String date = app.getDateApplied();
            if (date != null && !date.isEmpty()) {
                // If it's a full timestamp or ISO, take the date part (yyyy-MM-dd)
                if (date.contains("T")) {
                    date = date.split("T")[0];
                } else if (date.contains(" ")) {
                    date = date.split(" ")[0];
                }
                timelineCounts.put(date, timelineCounts.getOrDefault(date, 0L) + 1);
            }
        }

        Map<String, Object> stats = new HashMap<>();
        stats.put("totalApplications", totalCount);
        stats.put("statusDistribution", statusCounts);
        stats.put("applicationTimeline", timelineCounts);

        return ResponseEntity.ok(stats);
    }
}
