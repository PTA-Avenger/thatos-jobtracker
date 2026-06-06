-- ==========================================================================
-- MultiLang Job Tracker Database Schema (PostgreSQL / Supabase Version)
-- ==========================================================================

-- Clean reset of tables (Drops child tables first to avoid foreign key errors)
DROP TABLE IF EXISTS contacts;
DROP TABLE IF EXISTS notes;
DROP TABLE IF EXISTS applications;
DROP TABLE IF EXISTS jobs;
DROP TABLE IF EXISTS users;

-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    password VARCHAR(120) NOT NULL,
    CONSTRAINT UQ_users_username UNIQUE (username)
);

-- 2. Jobs Table (Scraped & Imported Listings)
CREATE TABLE IF NOT EXISTS jobs (
    id BIGSERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    company VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    description TEXT,
    skills TEXT, -- Comma-separated list of extracted skills
    url VARCHAR(255),
    date_posted VARCHAR(50),
    date_scraped VARCHAR(50),
    job_hash VARCHAR(255) NOT NULL,
    CONSTRAINT UQ_jobs_job_hash UNIQUE (job_hash)
);

-- 3. Applications Table (User Kanban Tracking Cards)
CREATE TABLE IF NOT EXISTS applications (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    job_id BIGINT NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'Saved', -- Saved, Applied, Interview, Offer, Rejected
    date_applied VARCHAR(50),
    cv_file_path VARCHAR(255),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
    CONSTRAINT UQ_user_job UNIQUE (user_id, job_id)
);

-- 4. Notes Table (Comments linked to applications)
CREATE TABLE IF NOT EXISTS notes (
    id BIGSERIAL PRIMARY KEY,
    application_id BIGINT NOT NULL,
    content TEXT NOT NULL,
    date_created VARCHAR(50) NOT NULL,
    FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE
);

-- 5. Contacts Table (Interviewers / Recruiters linked to applications)
CREATE TABLE IF NOT EXISTS contacts (
    id BIGSERIAL PRIMARY KEY,
    application_id BIGINT NOT NULL,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE
);

-- Indices for performance optimization
CREATE INDEX IF NOT EXISTS idx_jobs_job_hash ON jobs(job_hash);
CREATE INDEX IF NOT EXISTS idx_applications_user ON applications(user_id);
CREATE INDEX IF NOT EXISTS idx_notes_application ON notes(application_id);
CREATE INDEX IF NOT EXISTS idx_contacts_application ON contacts(application_id);
