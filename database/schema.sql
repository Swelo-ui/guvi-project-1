-- Operation Iron-Mask: Honeypot Database Schema
-- Run this in your InsForge SQL editor

-- Table: personas (stores consistent victim personas per session)
CREATE TABLE IF NOT EXISTS personas (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id TEXT UNIQUE NOT NULL,
    name TEXT,
    age INTEGER,
    city TEXT,
    bank_name TEXT,
    account_number TEXT,
    ifsc TEXT,
    upi_id TEXT,
    phone TEXT,
    persona_json JSONB,
    message_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_activity TIMESTAMPTZ DEFAULT NOW()
);

-- Table: conversations (stores all messages)
CREATE TABLE IF NOT EXISTS conversations (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id TEXT NOT NULL,
    sender TEXT NOT NULL CHECK (sender IN ('scammer', 'agent')),
    message TEXT,
    strategy_used TEXT,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Table: intelligence (extracted scammer data)
CREATE TABLE IF NOT EXISTS intelligence (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id TEXT NOT NULL,
    scammer_upi TEXT[],
    scammer_bank TEXT[],
    scammer_phone TEXT[],
    phishing_links TEXT[],
    scam_keywords TEXT[],
    scam_detected BOOLEAN DEFAULT TRUE,
    agent_notes TEXT,
    callback_sent BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_personas_session_id ON personas(session_id);
CREATE INDEX IF NOT EXISTS idx_conversations_session_id ON conversations(session_id);
CREATE INDEX IF NOT EXISTS idx_intelligence_session_id ON intelligence(session_id);
CREATE INDEX IF NOT EXISTS idx_intelligence_callback ON intelligence(callback_sent) WHERE callback_sent = FALSE;
