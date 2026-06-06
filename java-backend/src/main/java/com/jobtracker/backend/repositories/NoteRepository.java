package com.jobtracker.backend.repositories;

import com.jobtracker.backend.entities.Note;
import com.jobtracker.backend.entities.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.Optional;

@Repository
public interface NoteRepository extends JpaRepository<Note, Long> {
    Optional<Note> findByIdAndApplicationUser(Long id, User user);
}
