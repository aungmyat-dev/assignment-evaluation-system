CREATE DATABASE IF NOT EXISTS assignment_evaluation CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE assignment_evaluation;

CREATE TABLE users (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(120) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('student', 'teacher') NOT NULL DEFAULT 'student',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_users_role (role)
) ENGINE=InnoDB;

CREATE TABLE assignments (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    teacher_id INT UNSIGNED NOT NULL,
    title VARCHAR(180) NOT NULL,
    description TEXT NULL,
    reference_answer LONGTEXT NULL,
    keywords JSON NULL,
    rubric JSON NULL,
    min_words INT UNSIGNED NOT NULL DEFAULT 150,
    max_words INT UNSIGNED NOT NULL DEFAULT 2000,
    due_date DATETIME NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_assignments_teacher FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_assignments_teacher (teacher_id)
) ENGINE=InnoDB;

CREATE TABLE submissions (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    assignment_id INT UNSIGNED NOT NULL,
    student_id INT UNSIGNED NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    stored_filename VARCHAR(255) NOT NULL,
    extracted_text LONGTEXT NOT NULL,
    status ENUM('processing', 'evaluated', 'flagged', 'approved', 'overridden', 'failed') NOT NULL DEFAULT 'processing',
    submitted_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    evaluated_at DATETIME NULL,
    CONSTRAINT fk_submissions_assignment FOREIGN KEY (assignment_id) REFERENCES assignments(id) ON DELETE CASCADE,
    CONSTRAINT fk_submissions_student FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY uq_assignment_student_submission (assignment_id, student_id),
    INDEX idx_submissions_status (status),
    INDEX idx_submissions_student (student_id)
) ENGINE=InnoDB;

CREATE TABLE evaluation_results (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    submission_id INT UNSIGNED NOT NULL UNIQUE,
    predicted_score DECIMAL(5,2) NOT NULL,
    final_score DECIMAL(5,2) NULL,
    keyword_coverage DECIMAL(5,2) NOT NULL DEFAULT 0,
    reference_similarity DECIMAL(5,2) NOT NULL DEFAULT 0,
    vocabulary_richness DECIMAL(5,2) NOT NULL DEFAULT 0,
    word_count_score DECIMAL(5,2) NOT NULL DEFAULT 0,
    plagiarism_risk DECIMAL(5,2) NOT NULL DEFAULT 0,
    feedback JSON NULL,
    teacher_comment TEXT NULL,
    approved_by INT UNSIGNED NULL,
    approved_at DATETIME NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_results_submission FOREIGN KEY (submission_id) REFERENCES submissions(id) ON DELETE CASCADE,
    CONSTRAINT fk_results_approver FOREIGN KEY (approved_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_results_score (predicted_score),
    INDEX idx_results_risk (plagiarism_risk)
) ENGINE=InnoDB;

CREATE TABLE plagiarism_matches (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    submission_id INT UNSIGNED NOT NULL,
    compared_submission_id INT UNSIGNED NOT NULL,
    similarity_score DECIMAL(5,2) NOT NULL,
    matching_phrases JSON NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_matches_submission FOREIGN KEY (submission_id) REFERENCES submissions(id) ON DELETE CASCADE,
    CONSTRAINT fk_matches_compared FOREIGN KEY (compared_submission_id) REFERENCES submissions(id) ON DELETE CASCADE,
    UNIQUE KEY uq_plagiarism_pair (submission_id, compared_submission_id),
    INDEX idx_matches_score (similarity_score)
) ENGINE=InnoDB;
