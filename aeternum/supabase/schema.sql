-- Aeternum Main Database Schema

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Profiles Table
CREATE TABLE profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    role TEXT NOT NULL CHECK (role IN ('admin', 'student')),
    institution_name TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Exams Table
CREATE TABLE exams (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    subject TEXT,
    duration_mins INTEGER NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE,
    end_time TIMESTAMP WITH TIME ZONE,
    admin_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    questions JSONB,
    proctoring_config JSONB,
    status TEXT DEFAULT 'draft',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Sessions Table
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    exam_id UUID NOT NULL REFERENCES exams(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    integrity_score INTEGER DEFAULT 100,
    phone_verified BOOLEAN DEFAULT FALSE,
    status TEXT DEFAULT 'active'
);

-- Events Table
CREATE TABLE events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    metadata JSONB,
    screenshot_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Phone Tokens Table
CREATE TABLE phone_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    token TEXT NOT NULL UNIQUE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    connected BOOLEAN DEFAULT FALSE
);

-- Row Level Security (RLS) Policies

ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE exams ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE events ENABLE ROW LEVEL SECURITY;
ALTER TABLE phone_tokens ENABLE ROW LEVEL SECURITY;

-- Profiles: Admins can view own profile. Students can view own profile.
CREATE POLICY "Users can view own profile." ON profiles FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can update own profile." ON profiles FOR UPDATE USING (auth.uid() = id);

-- Exams: Admins can manage their own exams. Students can view active exams they are part of.
CREATE POLICY "Admins manage their exams." ON exams FOR ALL USING (auth.uid() = admin_id);
CREATE POLICY "Students can view exams." ON exams FOR SELECT USING (
    EXISTS (SELECT 1 FROM sessions WHERE sessions.exam_id = exams.id AND sessions.student_id = auth.uid())
);

-- Sessions: Students manage their own. Admins can view sessions for their exams.
CREATE POLICY "Students manage own sessions." ON sessions FOR ALL USING (auth.uid() = student_id);
CREATE POLICY "Admins view exam sessions." ON sessions FOR SELECT USING (
    EXISTS (SELECT 1 FROM exams WHERE exams.id = sessions.exam_id AND exams.admin_id = auth.uid())
);

-- Events: Students insert own events. Admins can view events for their exams.
CREATE POLICY "Students manage own events." ON events FOR ALL USING (
    EXISTS (SELECT 1 FROM sessions WHERE sessions.id = events.session_id AND sessions.student_id = auth.uid())
);
CREATE POLICY "Admins view exam events." ON events FOR SELECT USING (
    EXISTS (SELECT 1 FROM sessions JOIN exams ON sessions.exam_id = exams.id WHERE sessions.id = events.session_id AND exams.admin_id = auth.uid())
);

-- Phone tokens: Managed by the system, readable by session owners
CREATE POLICY "Students view phone tokens." ON phone_tokens FOR SELECT USING (
    EXISTS (SELECT 1 FROM sessions WHERE sessions.id = phone_tokens.session_id AND sessions.student_id = auth.uid())
);
