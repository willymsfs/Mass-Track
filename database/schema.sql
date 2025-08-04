-- Mass Tracking System Database Schema
-- Author: Manus AI
-- Date: January 8, 2025
-- Description: Complete database schema for priest mass tracking system

-- Enable UUID extension for unique identifiers
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pgcrypto for password hashing
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Users table for priest authentication and profiles
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    ordination_date DATE,
    current_assignment VARCHAR(255),
    diocese VARCHAR(255),
    province VARCHAR(255),
    phone VARCHAR(20),
    address TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    profile_image_url VARCHAR(500),
    preferences JSONB DEFAULT '{}',
    
    -- Constraints
    CONSTRAINT valid_email CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
    CONSTRAINT valid_username CHECK (username ~* '^[a-zA-Z0-9._-]{3,50}$')
);

-- Mass intentions table for all types of intentions
CREATE TABLE mass_intentions (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    intention_type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    source VARCHAR(100) NOT NULL,
    source_contact JSONB,
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    assigned_to INTEGER REFERENCES users(id) ON DELETE SET NULL,
    priority INTEGER DEFAULT 1,
    is_fixed_date BOOLEAN DEFAULT FALSE,
    fixed_date DATE,
    deadline_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Constraints
    CONSTRAINT valid_intention_type CHECK (intention_type IN ('personal', 'bulk', 'fixed_date', 'special', 'anniversary', 'birthday', 'deceased')),
    CONSTRAINT valid_priority CHECK (priority BETWEEN 1 AND 10),
    CONSTRAINT valid_source CHECK (source IN ('personal', 'province', 'generalate', 'parish', 'individual', 'family', 'organization'))
);

-- Bulk intentions table for managing large sets of masses
CREATE TABLE bulk_intentions (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    intention_id INTEGER REFERENCES mass_intentions(id) ON DELETE CASCADE,
    priest_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    total_count INTEGER NOT NULL,
    current_count INTEGER NOT NULL,
    completed_count INTEGER DEFAULT 0,
    start_date DATE NOT NULL,
    estimated_end_date DATE,
    actual_end_date DATE,
    is_paused BOOLEAN DEFAULT FALSE,
    pause_reason VARCHAR(255),
    paused_at TIMESTAMP WITH TIME ZONE,
    paused_count INTEGER,
    resume_count INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    notes TEXT,
    
    -- Constraints
    CONSTRAINT valid_counts CHECK (total_count > 0 AND current_count >= 0 AND completed_count >= 0),
    CONSTRAINT valid_completion CHECK (completed_count <= total_count),
    CONSTRAINT valid_current CHECK (current_count <= total_count),
    CONSTRAINT pause_logic CHECK (
        (is_paused = FALSE AND pause_reason IS NULL AND paused_at IS NULL) OR
        (is_paused = TRUE AND pause_reason IS NOT NULL AND paused_at IS NOT NULL)
    )
);

-- Mass celebrations table for recording actual celebrations
CREATE TABLE mass_celebrations (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    priest_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    celebration_date DATE NOT NULL,
    intention_id INTEGER REFERENCES mass_intentions(id) ON DELETE SET NULL,
    bulk_intention_id INTEGER REFERENCES bulk_intentions(id) ON DELETE SET NULL,
    serial_number INTEGER,
    mass_time TIME,
    location VARCHAR(255),
    notes TEXT,
    attendees_count INTEGER,
    special_circumstances TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    imported_from_excel BOOLEAN DEFAULT FALSE,
    import_batch_id UUID,
    
    -- Constraints
    CONSTRAINT valid_attendees CHECK (attendees_count >= 0),
    CONSTRAINT valid_serial_number CHECK (serial_number > 0),
    CONSTRAINT celebration_date_not_future CHECK (celebration_date <= CURRENT_DATE)
);

-- Monthly obligations table for tracking personal masses
CREATE TABLE monthly_obligations (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    priest_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    completed_count INTEGER DEFAULT 0,
    target_count INTEGER DEFAULT 3,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT valid_month CHECK (month BETWEEN 1 AND 12),
    CONSTRAINT valid_year CHECK (year BETWEEN 2000 AND 2100),
    CONSTRAINT valid_completed_count CHECK (completed_count BETWEEN 0 AND target_count),
    CONSTRAINT valid_target_count CHECK (target_count > 0),
    
    -- Unique constraint
    UNIQUE(priest_id, year, month)
);

-- Personal mass celebrations linking table
CREATE TABLE personal_mass_celebrations (
    id SERIAL PRIMARY KEY,
    monthly_obligation_id INTEGER REFERENCES monthly_obligations(id) ON DELETE CASCADE,
    mass_celebration_id INTEGER REFERENCES mass_celebrations(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Unique constraint to prevent double counting
    UNIQUE(monthly_obligation_id, mass_celebration_id)
);

-- Pause events table for tracking bulk intention pauses
CREATE TABLE pause_events (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    bulk_intention_id INTEGER REFERENCES bulk_intentions(id) ON DELETE CASCADE,
    event_type VARCHAR(20) NOT NULL,
    event_date DATE NOT NULL,
    reason VARCHAR(255),
    count_at_event INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    notes TEXT,
    
    -- Constraints
    CONSTRAINT valid_event_type CHECK (event_type IN ('pause', 'resume')),
    CONSTRAINT valid_count CHECK (count_at_event >= 0)
);

-- Excel import batches table for tracking data imports
CREATE TABLE excel_import_batches (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    priest_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    import_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    total_records INTEGER NOT NULL,
    successful_imports INTEGER DEFAULT 0,
    failed_imports INTEGER DEFAULT 0,
    year_range_start INTEGER,
    year_range_end INTEGER,
    status VARCHAR(20) DEFAULT 'processing',
    error_log TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT valid_status CHECK (status IN ('processing', 'completed', 'failed', 'partial')),
    CONSTRAINT valid_records CHECK (total_records > 0),
    CONSTRAINT valid_year_range CHECK (year_range_start <= year_range_end)
);

-- Special occasions table for recurring events
CREATE TABLE special_occasions (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    priest_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    occasion_type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    recurring_date DATE, -- For annual events (MM-DD format stored as date)
    specific_date DATE,  -- For one-time events
    is_recurring BOOLEAN DEFAULT FALSE,
    priority INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Constraints
    CONSTRAINT valid_occasion_type CHECK (occasion_type IN ('birthday', 'death_anniversary', 'ordination_anniversary', 'other')),
    CONSTRAINT valid_priority CHECK (priority BETWEEN 1 AND 10),
    CONSTRAINT date_logic CHECK (
        (is_recurring = TRUE AND recurring_date IS NOT NULL AND specific_date IS NULL) OR
        (is_recurring = FALSE AND specific_date IS NOT NULL AND recurring_date IS NULL)
    )
);

-- Notifications table for system alerts and reminders
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    priest_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    notification_type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    priority VARCHAR(20) DEFAULT 'normal',
    scheduled_for TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    read_at TIMESTAMP WITH TIME ZONE,
    related_entity_type VARCHAR(50),
    related_entity_id INTEGER,
    
    -- Constraints
    CONSTRAINT valid_notification_type CHECK (notification_type IN ('reminder', 'warning', 'info', 'success', 'error')),
    CONSTRAINT valid_priority CHECK (priority IN ('low', 'normal', 'high', 'urgent'))
);

-- System settings table for application configuration
CREATE TABLE system_settings (
    id SERIAL PRIMARY KEY,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT NOT NULL,
    setting_type VARCHAR(20) DEFAULT 'string',
    description TEXT,
    is_public BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT valid_setting_type CHECK (setting_type IN ('string', 'number', 'boolean', 'json'))
);

-- Audit log table for tracking important changes
CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id INTEGER NOT NULL,
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT valid_action CHECK (action IN ('create', 'update', 'delete', 'login', 'logout', 'import'))
);

-- Create indexes for performance optimization
CREATE INDEX idx_users_username_active ON users(username) WHERE is_active = TRUE;
CREATE INDEX idx_users_email_active ON users(email) WHERE is_active = TRUE;
CREATE INDEX idx_users_last_login ON users(last_login DESC);

CREATE INDEX idx_mass_intentions_type_active ON mass_intentions(intention_type) WHERE is_active = TRUE;
CREATE INDEX idx_mass_intentions_assigned_to ON mass_intentions(assigned_to) WHERE is_active = TRUE;
CREATE INDEX idx_mass_intentions_fixed_date ON mass_intentions(fixed_date) WHERE is_fixed_date = TRUE;

CREATE INDEX idx_bulk_intentions_priest_active ON bulk_intentions(priest_id, is_paused, current_count) WHERE current_count > 0;
CREATE INDEX idx_bulk_intentions_completion ON bulk_intentions(priest_id, actual_end_date) WHERE actual_end_date IS NULL;

CREATE INDEX idx_mass_celebrations_priest_date ON mass_celebrations(priest_id, celebration_date DESC);
CREATE INDEX idx_mass_celebrations_bulk_intention ON mass_celebrations(bulk_intention_id, serial_number DESC);
CREATE INDEX idx_mass_celebrations_date_range ON mass_celebrations(celebration_date) WHERE celebration_date >= '2000-01-01';

CREATE INDEX idx_monthly_obligations_priest_period ON monthly_obligations(priest_id, year DESC, month DESC);
CREATE INDEX idx_monthly_obligations_incomplete ON monthly_obligations(priest_id, year, month) WHERE completed_count < target_count;

CREATE INDEX idx_pause_events_bulk_intention ON pause_events(bulk_intention_id, event_date DESC);

CREATE INDEX idx_notifications_priest_unread ON notifications(priest_id, created_at DESC) WHERE is_read = FALSE;
CREATE INDEX idx_notifications_scheduled ON notifications(scheduled_for) WHERE scheduled_for IS NOT NULL AND is_read = FALSE;

CREATE INDEX idx_audit_log_user_action ON audit_log(user_id, action, created_at DESC);
CREATE INDEX idx_audit_log_entity ON audit_log(entity_type, entity_id, created_at DESC);

-- Create GIN indexes for JSONB columns
CREATE INDEX idx_mass_intentions_metadata ON mass_intentions USING GIN(metadata);
CREATE INDEX idx_users_preferences ON users USING GIN(preferences);

-- Create triggers for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update triggers to relevant tables
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_mass_intentions_updated_at BEFORE UPDATE ON mass_intentions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_bulk_intentions_updated_at BEFORE UPDATE ON bulk_intentions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_mass_celebrations_updated_at BEFORE UPDATE ON mass_celebrations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_monthly_obligations_updated_at BEFORE UPDATE ON monthly_obligations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_special_occasions_updated_at BEFORE UPDATE ON special_occasions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_system_settings_updated_at BEFORE UPDATE ON system_settings FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default system settings
INSERT INTO system_settings (setting_key, setting_value, setting_type, description, is_public) VALUES
('app_name', 'Mass Tracking System', 'string', 'Application name', TRUE),
('app_version', '1.0.0', 'string', 'Application version', TRUE),
('monthly_personal_mass_target', '3', 'number', 'Default number of personal masses required per month', TRUE),
('bulk_intention_warning_threshold', '10', 'number', 'Show warning when bulk intentions have this many or fewer remaining', TRUE),
('max_excel_import_records', '10000', 'number', 'Maximum number of records allowed in Excel import', FALSE),
('session_timeout_minutes', '480', 'number', 'Session timeout in minutes (8 hours)', FALSE),
('password_min_length', '8', 'number', 'Minimum password length', TRUE),
('enable_email_notifications', 'false', 'boolean', 'Enable email notifications', TRUE),
('import_year_range_start', '2000', 'number', 'Earliest year allowed for data import', TRUE),
('import_year_range_end', '2030', 'number', 'Latest year allowed for data import', TRUE);

-- Create views for common queries
CREATE VIEW active_bulk_intentions AS
SELECT 
    bi.*,
    mi.title as intention_title,
    mi.description as intention_description,
    u.full_name as priest_name,
    ROUND((bi.completed_count::DECIMAL / bi.total_count) * 100, 2) as completion_percentage,
    CASE 
        WHEN bi.current_count <= 10 THEN 'warning'
        WHEN bi.current_count <= 5 THEN 'critical'
        ELSE 'normal'
    END as status_level
FROM bulk_intentions bi
JOIN mass_intentions mi ON bi.intention_id = mi.id
JOIN users u ON bi.priest_id = u.id
WHERE bi.current_count > 0 AND mi.is_active = TRUE;

CREATE VIEW monthly_progress_summary AS
SELECT 
    mo.*,
    u.full_name as priest_name,
    ROUND((mo.completed_count::DECIMAL / mo.target_count) * 100, 2) as completion_percentage,
    CASE 
        WHEN mo.completed_count >= mo.target_count THEN 'completed'
        WHEN mo.completed_count >= (mo.target_count * 0.67) THEN 'on_track'
        WHEN EXTRACT(DAY FROM DATE(mo.year || '-' || mo.month || '-01') + INTERVAL '1 month' - INTERVAL '1 day') - EXTRACT(DAY FROM CURRENT_DATE) <= 7 THEN 'urgent'
        ELSE 'behind'
    END as status
FROM monthly_obligations mo
JOIN users u ON mo.priest_id = u.id
WHERE mo.year = EXTRACT(YEAR FROM CURRENT_DATE) 
   OR (mo.year = EXTRACT(YEAR FROM CURRENT_DATE) - 1 AND mo.month = 12 AND EXTRACT(MONTH FROM CURRENT_DATE) = 1);

CREATE VIEW recent_celebrations AS
SELECT 
    mc.*,
    u.full_name as priest_name,
    mi.title as intention_title,
    mi.intention_type,
    bi.total_count as bulk_total,
    bi.current_count as bulk_remaining
FROM mass_celebrations mc
JOIN users u ON mc.priest_id = u.id
LEFT JOIN mass_intentions mi ON mc.intention_id = mi.id
LEFT JOIN bulk_intentions bi ON mc.bulk_intention_id = bi.id
WHERE mc.celebration_date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY mc.celebration_date DESC, mc.created_at DESC;

-- Create function for bulk intention countdown
CREATE OR REPLACE FUNCTION update_bulk_intention_count(
    p_bulk_intention_id INTEGER,
    p_celebration_date DATE
) RETURNS BOOLEAN AS $$
DECLARE
    v_current_count INTEGER;
    v_is_paused BOOLEAN;
BEGIN
    -- Get current state
    SELECT current_count, is_paused 
    INTO v_current_count, v_is_paused
    FROM bulk_intentions 
    WHERE id = p_bulk_intention_id;
    
    -- Check if bulk intention exists and is not paused
    IF v_current_count IS NULL THEN
        RAISE EXCEPTION 'Bulk intention not found';
    END IF;
    
    IF v_is_paused THEN
        RAISE EXCEPTION 'Cannot update paused bulk intention';
    END IF;
    
    IF v_current_count <= 0 THEN
        RAISE EXCEPTION 'Bulk intention already completed';
    END IF;
    
    -- Update counts
    UPDATE bulk_intentions 
    SET 
        current_count = current_count - 1,
        completed_count = completed_count + 1,
        updated_at = NOW(),
        actual_end_date = CASE WHEN current_count - 1 = 0 THEN p_celebration_date ELSE actual_end_date END
    WHERE id = p_bulk_intention_id;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Create function for pausing bulk intentions
CREATE OR REPLACE FUNCTION pause_bulk_intention(
    p_bulk_intention_id INTEGER,
    p_reason VARCHAR(255)
) RETURNS BOOLEAN AS $$
BEGIN
    -- Update bulk intention
    UPDATE bulk_intentions 
    SET 
        is_paused = TRUE,
        pause_reason = p_reason,
        paused_at = NOW(),
        paused_count = current_count,
        updated_at = NOW()
    WHERE id = p_bulk_intention_id AND is_paused = FALSE;
    
    -- Log pause event
    INSERT INTO pause_events (bulk_intention_id, event_type, event_date, reason, count_at_event)
    SELECT id, 'pause', CURRENT_DATE, p_reason, current_count
    FROM bulk_intentions 
    WHERE id = p_bulk_intention_id;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Create function for resuming bulk intentions
CREATE OR REPLACE FUNCTION resume_bulk_intention(
    p_bulk_intention_id INTEGER
) RETURNS BOOLEAN AS $$
BEGIN
    -- Update bulk intention
    UPDATE bulk_intentions 
    SET 
        is_paused = FALSE,
        pause_reason = NULL,
        paused_at = NULL,
        resume_count = current_count,
        updated_at = NOW()
    WHERE id = p_bulk_intention_id AND is_paused = TRUE;
    
    -- Log resume event
    INSERT INTO pause_events (bulk_intention_id, event_type, event_date, count_at_event)
    SELECT id, 'resume', CURRENT_DATE, current_count
    FROM bulk_intentions 
    WHERE id = p_bulk_intention_id;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Create function for updating monthly obligations
CREATE OR REPLACE FUNCTION update_monthly_obligation(
    p_priest_id INTEGER,
    p_celebration_date DATE,
    p_mass_celebration_id INTEGER
) RETURNS BOOLEAN AS $$
DECLARE
    v_year INTEGER;
    v_month INTEGER;
    v_obligation_id INTEGER;
    v_current_count INTEGER;
    v_target_count INTEGER;
BEGIN
    -- Extract year and month from celebration date
    v_year := EXTRACT(YEAR FROM p_celebration_date);
    v_month := EXTRACT(MONTH FROM p_celebration_date);
    
    -- Get or create monthly obligation
    INSERT INTO monthly_obligations (priest_id, year, month)
    VALUES (p_priest_id, v_year, v_month)
    ON CONFLICT (priest_id, year, month) DO NOTHING;
    
    -- Get obligation details
    SELECT id, completed_count, target_count
    INTO v_obligation_id, v_current_count, v_target_count
    FROM monthly_obligations
    WHERE priest_id = p_priest_id AND year = v_year AND month = v_month;
    
    -- Check if we can add another personal mass
    IF v_current_count >= v_target_count THEN
        RAISE EXCEPTION 'Monthly personal mass limit already reached';
    END IF;
    
    -- Link the celebration to the obligation
    INSERT INTO personal_mass_celebrations (monthly_obligation_id, mass_celebration_id)
    VALUES (v_obligation_id, p_mass_celebration_id);
    
    -- Update the count
    UPDATE monthly_obligations
    SET completed_count = completed_count + 1, updated_at = NOW()
    WHERE id = v_obligation_id;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions (adjust as needed for your deployment)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO mass_tracking_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO mass_tracking_user;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO mass_tracking_user;

COMMENT ON DATABASE postgres IS 'Mass Tracking System Database - Manages priest mass celebration records and intentions';

