package com.jobtracker.backend.controllers;

import com.jobtracker.backend.entities.*;
import com.jobtracker.backend.repositories.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/applications")
public class ApplicationController {

    @Autowired
    private ApplicationRepository applicationRepository;

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private JobRepository jobRepository;

    @Autowired
    private NoteRepository noteRepository;

    @Autowired
    private ContactRepository contactRepository;

    private User getAuthenticatedUser() {
        String username = SecurityContextHolder.getContext().getAuthentication().getName();
        return userRepository.findByUsername(username)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.UNAUTHORIZED, "User not found"));
    }

    @GetMapping
    public ResponseEntity<List<Application>> getApplications() {
        User user = getAuthenticatedUser();
        List<Application> applications = applicationRepository.findByUser(user);
        return ResponseEntity.ok(applications);
    }

    @GetMapping("/{id}")
    public ResponseEntity<Application> getApplicationById(@PathVariable Long id) {
        User user = getAuthenticatedUser();
        Application application = applicationRepository.findByIdAndUser(id, user)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Application not found"));
        return ResponseEntity.ok(application);
    }

    @PostMapping
    public ResponseEntity<?> createApplication(@RequestBody CreateApplicationRequest request) {
        User user = getAuthenticatedUser();
        Job job = jobRepository.findById(request.getJobId())
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Job not found"));

        if (applicationRepository.existsByUserAndJob(user, job)) {
            return ResponseEntity.badRequest().body(Map.of("message", "You have already tracked this job application!"));
        }

        String status = request.getStatus() != null ? request.getStatus() : "Saved";
        String dateApplied = request.getDateApplied() != null ? request.getDateApplied() : LocalDateTime.now().format(DateTimeFormatter.ISO_LOCAL_DATE);

        Application application = new Application(user, job, status, dateApplied, request.getCvFilePath());
        Application saved = applicationRepository.save(application);
        return ResponseEntity.status(HttpStatus.CREATED).body(saved);
    }

    @PutMapping("/{id}/status")
    public ResponseEntity<Application> updateStatus(@PathVariable Long id, @RequestBody UpdateStatusRequest request) {
        User user = getAuthenticatedUser();
        Application application = applicationRepository.findByIdAndUser(id, user)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Application not found"));

        application.setStatus(request.getStatus());
        Application updated = applicationRepository.save(application);
        return ResponseEntity.ok(updated);
    }

    @PutMapping("/{id}/cv")
    public ResponseEntity<Application> updateCvPath(@PathVariable Long id, @RequestBody UpdateCvRequest request) {
        User user = getAuthenticatedUser();
        Application application = applicationRepository.findByIdAndUser(id, user)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Application not found"));

        application.setCvFilePath(request.getCvFilePath());
        Application updated = applicationRepository.save(application);
        return ResponseEntity.ok(updated);
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<?> deleteApplication(@PathVariable Long id) {
        User user = getAuthenticatedUser();
        Application application = applicationRepository.findByIdAndUser(id, user)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Application not found"));

        applicationRepository.delete(application);
        return ResponseEntity.ok(Map.of("message", "Application deleted successfully"));
    }

    // --- Notes Sub-Resources ---

    @PostMapping("/{id}/notes")
    public ResponseEntity<Note> addNote(@PathVariable Long id, @RequestBody CreateNoteRequest request) {
        User user = getAuthenticatedUser();
        Application application = applicationRepository.findByIdAndUser(id, user)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Application not found"));

        Note note = new Note(application, request.getContent(), LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss")));
        Note savedNote = noteRepository.save(note);
        return ResponseEntity.status(HttpStatus.CREATED).body(savedNote);
    }

    @DeleteMapping("/notes/{noteId}")
    public ResponseEntity<?> deleteNote(@PathVariable Long noteId) {
        User user = getAuthenticatedUser();
        Note note = noteRepository.findByIdAndApplicationUser(noteId, user)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Note not found or unauthorized"));

        noteRepository.delete(note);
        return ResponseEntity.ok(Map.of("message", "Note deleted successfully"));
    }

    // --- Contacts Sub-Resources ---

    @PostMapping("/{id}/contacts")
    public ResponseEntity<Contact> addContact(@PathVariable Long id, @RequestBody CreateContactRequest request) {
        User user = getAuthenticatedUser();
        Application application = applicationRepository.findByIdAndUser(id, user)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Application not found"));

        Contact contact = new Contact(application, request.getName(), request.getRole(), request.getEmail(), request.getPhone());
        Contact savedContact = contactRepository.save(contact);
        return ResponseEntity.status(HttpStatus.CREATED).body(savedContact);
    }

    @DeleteMapping("/contacts/{contactId}")
    public ResponseEntity<?> deleteContact(@PathVariable Long contactId) {
        User user = getAuthenticatedUser();
        Contact contact = contactRepository.findByIdAndApplicationUser(contactId, user)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Contact not found or unauthorized"));

        contactRepository.delete(contact);
        return ResponseEntity.ok(Map.of("message", "Contact deleted successfully"));
    }

    // --- DTO Classes ---

    public static class CreateApplicationRequest {
        private Long jobId;
        private String status;
        private String dateApplied;
        private String cvFilePath;

        public Long getJobId() { return jobId; }
        public void setJobId(Long jobId) { this.jobId = jobId; }
        public String getStatus() { return status; }
        public void setStatus(String status) { this.status = status; }
        public String getDateApplied() { return dateApplied; }
        public void setDateApplied(String dateApplied) { this.dateApplied = dateApplied; }
        public String getCvFilePath() { return cvFilePath; }
        public void setCvFilePath(String cvFilePath) { this.cvFilePath = cvFilePath; }
    }

    public static class UpdateStatusRequest {
        private String status;
        public String getStatus() { return status; }
        public void setStatus(String status) { this.status = status; }
    }

    public static class UpdateCvRequest {
        private String cvFilePath;
        public String getCvFilePath() { return cvFilePath; }
        public void setCvFilePath(String cvFilePath) { this.cvFilePath = cvFilePath; }
    }

    public static class CreateNoteRequest {
        private String content;
        public String getContent() { return content; }
        public void setContent(String content) { this.content = content; }
    }

    public static class CreateContactRequest {
        private String name;
        private String role;
        private String email;
        private String phone;

        public String getName() { return name; }
        public void setName(String name) { this.name = name; }
        public String getRole() { return role; }
        public void setRole(String role) { this.role = role; }
        public String getEmail() { return email; }
        public void setEmail(String email) { this.email = email; }
        public String getPhone() { return phone; }
        public void setPhone(String phone) { this.phone = phone; }
    }
}
