package com.jobtracker.backend.repositories;

import com.jobtracker.backend.entities.Application;
import com.jobtracker.backend.entities.User;
import com.jobtracker.backend.entities.Job;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.List;
import java.util.Optional;

@Repository
public interface ApplicationRepository extends JpaRepository<Application, Long> {
    List<Application> findByUser(User user);
    Optional<Application> findByIdAndUser(Long id, User user);
    Optional<Application> findByUserAndJob(User user, Job job);
    Boolean existsByUserAndJob(User user, Job job);
}
