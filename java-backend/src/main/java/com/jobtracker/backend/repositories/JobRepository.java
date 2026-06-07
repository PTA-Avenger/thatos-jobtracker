package com.jobtracker.backend.repositories;

import com.jobtracker.backend.entities.Job;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;
import java.util.Optional;

@Repository
public interface JobRepository extends JpaRepository<Job, Long> {
    Optional<Job> findByJobHash(String jobHash);
    Boolean existsByJobHash(String jobHash);

    @Query("SELECT j FROM Job j WHERE " +
           "(COALESCE(:skills, '') = '' OR LOWER(j.skills) LIKE LOWER(CONCAT('%', :skills, '%'))) AND " +
           "(COALESCE(:company, '') = '' OR LOWER(j.company) LIKE LOWER(CONCAT('%', :company, '%'))) AND " +
           "(COALESCE(:title, '') = '' OR LOWER(j.title) LIKE LOWER(CONCAT('%', :title, '%'))) AND " +
           "(:visaSponsorship IS NULL OR j.visaSponsorship = :visaSponsorship) AND " +
           "(:maxExperience IS NULL OR j.yearsExperienceRequired IS NULL OR j.yearsExperienceRequired <= :maxExperience) AND " +
           "(COALESCE(:sourcePlatform, '') = '' OR LOWER(j.sourcePlatform) = LOWER(:sourcePlatform))")
    Page<Job> findWithFilters(@Param("skills") String skills,
                              @Param("company") String company,
                              @Param("title") String title,
                              @Param("visaSponsorship") Boolean visaSponsorship,
                              @Param("maxExperience") Integer maxExperience,
                              @Param("sourcePlatform") String sourcePlatform,
                              Pageable pageable);
}
