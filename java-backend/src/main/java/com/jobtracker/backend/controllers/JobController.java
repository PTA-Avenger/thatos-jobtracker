package com.jobtracker.backend.controllers;

import com.jobtracker.backend.entities.Job;
import com.jobtracker.backend.repositories.JobRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/jobs")
public class JobController {

    @Autowired
    private JobRepository jobRepository;

    @Value("${scraper.key:ScraperSuperSecretKey123}")
    private String scraperKey;

    @GetMapping
    public ResponseEntity<Page<Job>> getJobs(
            @RequestParam(required = false) String skills,
            @RequestParam(required = false) String company,
            @RequestParam(required = false) String title,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "10") int size,
            @RequestParam(defaultValue = "id,desc") String[] sort) {

        List<Sort.Order> orders = new ArrayList<>();
        if (sort[0].contains(",")) {
            // sort = [field,direction]
            for (String sortOrder : sort) {
                String[] _sort = sortOrder.split(",");
                orders.add(new Sort.Order(Sort.Direction.fromString(_sort[1]), _sort[0]));
            }
        } else {
            // sort = [field, direction]
            orders.add(new Sort.Order(Sort.Direction.fromString(sort[1]), sort[0]));
        }

        Pageable pageable = PageRequest.of(page, size, Sort.by(orders));
        Page<Job> jobsPage = jobRepository.findWithFilters(skills, company, title, pageable);

        return ResponseEntity.ok(jobsPage);
    }

    @PostMapping("/import")
    public ResponseEntity<?> importJobs(
            @RequestHeader(value = "X-Scraper-Key", required = false) String key,
            @RequestBody List<Job> jobs) {

        if (key == null || !key.equals(scraperKey)) {
            return ResponseEntity.status(HttpStatus.FORBIDDEN)
                    .body(Map.of("message", "Forbidden: Invalid or missing X-Scraper-Key header"));
        }

        int importedCount = 0;
        int duplicateCount = 0;

        for (Job job : jobs) {
            if (job.getJobHash() == null) {
                // Generate fallback hash if scraper didn't provide one
                String fallbackHash = (job.getTitle() + "|" + job.getCompany() + "|" + job.getDatePosted()).toLowerCase();
                job.setJobHash(fallbackHash);
            }

            if (jobRepository.existsByJobHash(job.getJobHash())) {
                duplicateCount++;
            } else {
                jobRepository.save(job);
                importedCount++;
            }
        }

        return ResponseEntity.ok(Map.of(
                "message", "Jobs import processed successfully",
                "imported", importedCount,
                "duplicates_skipped", duplicateCount
        ));
    }
}
