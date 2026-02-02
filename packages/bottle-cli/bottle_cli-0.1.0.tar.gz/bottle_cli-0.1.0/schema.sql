-- Bottle CLI - Supabase Schema
-- Run this in your Supabase SQL editor

-- Users table
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    tokens REAL DEFAULT 3.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Projects table
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_code TEXT UNIQUE NOT NULL,
    user_id TEXT REFERENCES users(id),
    project_type TEXT,
    feedback_type TEXT CHECK (feedback_type IN ('idea', 'ux', 'code')),
    summary TEXT,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'reviewed')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Feedback table
CREATE TABLE feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_claim_code TEXT REFERENCES projects(claim_code),
    reviewer_id TEXT REFERENCES users(id),
    feedback_type TEXT,
    content TEXT NOT NULL,
    rating TEXT CHECK (rating IS NULL OR rating IN ('helpful', 'not_helpful')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_user ON projects(user_id);
CREATE INDEX idx_feedback_project ON feedback(project_claim_code);

-- Enable RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE feedback ENABLE ROW LEVEL SECURITY;

-- Policies (permissive for MVP - tighten for production)
CREATE POLICY "Allow all for users" ON users FOR ALL USING (true);
CREATE POLICY "Allow all for projects" ON projects FOR ALL USING (true);
CREATE POLICY "Allow all for feedback" ON feedback FOR ALL USING (true);

-- Storage bucket for project files
-- Run this in Supabase dashboard > Storage > Create bucket
-- Name: projects
-- Public: false