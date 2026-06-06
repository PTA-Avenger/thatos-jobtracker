package com.jobtracker.backend.repositories;

import com.jobtracker.backend.entities.Contact;
import com.jobtracker.backend.entities.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.Optional;

@Repository
public interface ContactRepository extends JpaRepository<Contact, Long> {
    Optional<Contact> findByIdAndApplicationUser(Long id, User user);
}
