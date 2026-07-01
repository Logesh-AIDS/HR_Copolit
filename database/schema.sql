-- database/schema.sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Recruiters table
CREATE TABLE IF NOT EXISTS recruiters (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Jobs table
CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    recruiter_id UUID REFERENCES recruiters(id) ON DELETE CASCADE NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    department VARCHAR(100),
    experience_level VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Candidates table
CREATE TABLE IF NOT EXISTS candidates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    resume_url TEXT NOT NULL,
    parsed_skills JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Applications table
CREATE TABLE IF NOT EXISTS applications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    candidate_id UUID REFERENCES candidates(id) ON DELETE CASCADE NOT NULL,
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE NOT NULL,
    status VARCHAR(50) DEFAULT 'APPLIED' NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT unique_candidate_job UNIQUE (candidate_id, job_id)
);

-- Active Sessions table
CREATE TABLE IF NOT EXISTS interview_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    application_id UUID REFERENCES applications(id) ON DELETE CASCADE NOT NULL,
    session_token VARCHAR(512) UNIQUE NOT NULL,
    status VARCHAR(50) DEFAULT 'PENDING' NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE,
    ended_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Questions Bank
CREATE TABLE IF NOT EXISTS questions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    category VARCHAR(100) NOT NULL,
    subcategory VARCHAR(100),
    difficulty VARCHAR(50) NOT NULL,
    problem_statement TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Attempts per Question
CREATE TABLE IF NOT EXISTS question_attempts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES interview_sessions(id) ON DELETE CASCADE NOT NULL,
    question_id UUID REFERENCES questions(id) ON DELETE RESTRICT NOT NULL,
    time_spent_seconds INT DEFAULT 0 NOT NULL,
    response_transcript TEXT,
    auto_score NUMERIC(5, 2),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Code Submissions inside attempts
CREATE TABLE IF NOT EXISTS code_submissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    question_attempt_id UUID REFERENCES question_attempts(id) ON DELETE CASCADE NOT NULL,
    source_code TEXT NOT NULL,
    language VARCHAR(50) NOT NULL,
    test_cases_passed INT NOT NULL,
    total_test_cases INT NOT NULL,
    execution_time_ms NUMERIC(10, 2),
    memory_used_bytes INT,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Proctoring log checks
CREATE TABLE IF NOT EXISTS proctoring_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES interview_sessions(id) ON DELETE CASCADE NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    anomaly_type VARCHAR(100) NOT NULL,
    confidence_score NUMERIC(5, 4) NOT NULL,
    details TEXT NOT NULL
);

-- Final Evaluation Reports
CREATE TABLE IF NOT EXISTS evaluation_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES interview_sessions(id) ON DELETE CASCADE UNIQUE NOT NULL,
    overall_score NUMERIC(4, 2) NOT NULL,
    technical_skills_matrix JSONB NOT NULL,
    behavioral_skills_matrix JSONB NOT NULL,
    summary_verdict TEXT NOT NULL,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Indexes for performance optimizations
CREATE INDEX IF NOT EXISTS idx_jobs_recruiter ON jobs(recruiter_id);
CREATE INDEX IF NOT EXISTS idx_candidates_email ON candidates(email);
CREATE INDEX IF NOT EXISTS idx_applications_job ON applications(job_id);
CREATE INDEX IF NOT EXISTS idx_sessions_token ON interview_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_attempts_session ON question_attempts(session_id);
CREATE INDEX IF NOT EXISTS idx_submissions_attempt ON code_submissions(question_attempt_id);
CREATE INDEX IF NOT EXISTS idx_proctor_session ON proctoring_logs(session_id);
