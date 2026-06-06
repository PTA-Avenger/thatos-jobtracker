package com.jobtracker.backend.entities;

import jakarta.persistence.*;

@Entity
@Table(name = "jobs", uniqueConstraints = {
    @UniqueConstraint(columnNames = "jobHash")
})
public class Job {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String title;
    private String company;
    private String location;

    @Column(columnDefinition = "TEXT")
    private String description;

    @Column(columnDefinition = "TEXT")
    private String skills; // Stored as comma-separated or JSON list of skills

    private String url;
    private String datePosted;
    private String dateScraped;

    private String jobHash; // Hashed value of title + company + datePosted for deduplication

    public Job() {}

    public Job(String title, String company, String location, String description, String skills, String url, String datePosted, String dateScraped, String jobHash) {
        this.title = title;
        this.company = company;
        this.location = location;
        this.description = description;
        this.skills = skills;
        this.url = url;
        this.datePosted = datePosted;
        this.dateScraped = dateScraped;
        this.jobHash = jobHash;
    }

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public String getTitle() {
        return title;
    }

    public void setTitle(String title) {
        this.title = title;
    }

    public String getCompany() {
        return company;
    }

    public void setCompany(String company) {
        this.company = company;
    }

    public String getLocation() {
        return location;
    }

    public void setLocation(String location) {
        this.location = location;
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    public String getSkills() {
        return skills;
    }

    public void setSkills(String skills) {
        this.skills = skills;
    }

    public String getUrl() {
        return url;
    }

    public void setUrl(String url) {
        this.url = url;
    }

    public String getDatePosted() {
        return datePosted;
    }

    public void setDatePosted(String datePosted) {
        this.datePosted = datePosted;
    }

    public String getDateScraped() {
        return dateScraped;
    }

    public void setDateScraped(String dateScraped) {
        this.dateScraped = dateScraped;
    }

    public String getJobHash() {
        return jobHash;
    }

    public void setJobHash(String jobHash) {
        this.jobHash = jobHash;
    }
}
