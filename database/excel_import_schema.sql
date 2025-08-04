-- Excel Import Functionality for Mass Tracking System
-- Author: Manus AI
-- Date: January 8, 2025
-- Description: Database schema and functions for importing historical mass data from Excel files

-- Create table for Excel import templates
CREATE TABLE excel_import_templates (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    template_name VARCHAR(100) NOT NULL,
    description TEXT,
    column_mappings JSONB NOT NULL,
    validation_rules JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Sample column mappings structure:
    -- {
    --   "date": "A",
    --   "time": "B", 
    --   "intention": "C",
    --   "location": "D",
    --   "notes": "E",
    --   "attendees": "F"
    -- }
    
    CONSTRAINT unique_template_name UNIQUE(template_name)
);

-- Create table for Excel import validation errors
CREATE TABLE excel_import_errors (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    import_batch_id UUID REFERENCES excel_import_batches(uuid) ON DELETE CASCADE,
    row_number INTEGER NOT NULL,
    column_name VARCHAR(100),
    error_type VARCHAR(50) NOT NULL,
    error_message TEXT NOT NULL,
    raw_value TEXT,
    suggested_value TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT valid_error_type CHECK (error_type IN ('validation', 'format', 'missing', 'duplicate', 'business_rule'))
);

-- Create table for Excel import field mappings
CREATE TABLE excel_import_field_mappings (
    id SERIAL PRIMARY KEY,
    import_batch_id UUID REFERENCES excel_import_batches(uuid) ON DELETE CASCADE,
    excel_column VARCHAR(10) NOT NULL,  -- A, B, C, etc.
    excel_header VARCHAR(255),
    database_field VARCHAR(100) NOT NULL,
    data_type VARCHAR(50) NOT NULL,
    is_required BOOLEAN DEFAULT FALSE,
    default_value TEXT,
    transformation_rule TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT valid_data_type CHECK (data_type IN ('date', 'time', 'text', 'number', 'boolean')),
    CONSTRAINT valid_database_field CHECK (database_field IN (
        'celebration_date', 'mass_time', 'intention_title', 'intention_description', 
        'intention_type', 'location', 'notes', 'attendees_count', 'source'
    ))
);

-- Insert default Excel import templates
INSERT INTO excel_import_templates (template_name, description, column_mappings, validation_rules) VALUES
('Standard Mass Log', 'Standard template for importing daily mass records', 
 '{
    "celebration_date": {"column": "A", "required": true, "format": "date"},
    "mass_time": {"column": "B", "required": false, "format": "time"},
    "intention_title": {"column": "C", "required": false, "format": "text"},
    "intention_description": {"column": "D", "required": false, "format": "text"},
    "location": {"column": "E", "required": false, "format": "text"},
    "notes": {"column": "F", "required": false, "format": "text"},
    "attendees_count": {"column": "G", "required": false, "format": "number"}
  }',
  '{
    "date_range": {"min": "2000-01-01", "max": "2030-12-31"},
    "required_fields": ["celebration_date"],
    "max_attendees": 10000,
    "allowed_locations": []
  }'
),
('Detailed Mass Record', 'Comprehensive template with all mass details',
 '{
    "celebration_date": {"column": "A", "required": true, "format": "date"},
    "mass_time": {"column": "B", "required": true, "format": "time"},
    "intention_title": {"column": "C", "required": true, "format": "text"},
    "intention_description": {"column": "D", "required": false, "format": "text"},
    "intention_type": {"column": "E", "required": false, "format": "text"},
    "source": {"column": "F", "required": false, "format": "text"},
    "location": {"column": "G", "required": true, "format": "text"},
    "notes": {"column": "H", "required": false, "format": "text"},
    "attendees_count": {"column": "I", "required": false, "format": "number"}
  }',
  '{
    "date_range": {"min": "2000-01-01", "max": "2030-12-31"},
    "required_fields": ["celebration_date", "mass_time", "intention_title", "location"],
    "max_attendees": 10000,
    "allowed_intention_types": ["personal", "special", "anniversary", "birthday", "deceased"],
    "allowed_sources": ["personal", "parish", "individual", "family", "organization"]
  }'
),
('Simple Mass Log', 'Minimal template for basic mass tracking',
 '{
    "celebration_date": {"column": "A", "required": true, "format": "date"},
    "intention_title": {"column": "B", "required": false, "format": "text"},
    "notes": {"column": "C", "required": false, "format": "text"}
  }',
  '{
    "date_range": {"min": "2000-01-01", "max": "2030-12-31"},
    "required_fields": ["celebration_date"]
  }'
);

-- Create function to validate Excel import data
CREATE OR REPLACE FUNCTION validate_excel_import_row(
    p_import_batch_id UUID,
    p_row_number INTEGER,
    p_row_data JSONB,
    p_template_id INTEGER DEFAULT NULL
) RETURNS BOOLEAN AS $$
DECLARE
    v_template RECORD;
    v_field_name TEXT;
    v_field_config JSONB;
    v_value TEXT;
    v_date_value DATE;
    v_time_value TIME;
    v_number_value NUMERIC;
    v_error_count INTEGER := 0;
BEGIN
    -- Get template configuration
    IF p_template_id IS NOT NULL THEN
        SELECT * INTO v_template FROM excel_import_templates WHERE id = p_template_id;
    ELSE
        SELECT * INTO v_template FROM excel_import_templates WHERE template_name = 'Standard Mass Log';
    END IF;
    
    -- Validate each field according to template
    FOR v_field_name, v_field_config IN SELECT * FROM jsonb_each(v_template.column_mappings)
    LOOP
        v_value := p_row_data ->> (v_field_config ->> 'column');
        
        -- Check required fields
        IF (v_field_config ->> 'required')::BOOLEAN = TRUE AND (v_value IS NULL OR v_value = '') THEN
            INSERT INTO excel_import_errors (import_batch_id, row_number, column_name, error_type, error_message, raw_value)
            VALUES (p_import_batch_id, p_row_number, v_field_name, 'missing', 
                   'Required field is missing or empty', v_value);
            v_error_count := v_error_count + 1;
            CONTINUE;
        END IF;
        
        -- Skip validation if value is empty and not required
        IF v_value IS NULL OR v_value = '' THEN
            CONTINUE;
        END IF;
        
        -- Validate data types
        CASE v_field_config ->> 'format'
            WHEN 'date' THEN
                BEGIN
                    v_date_value := v_value::DATE;
                    -- Check date range
                    IF v_date_value < '2000-01-01' OR v_date_value > '2030-12-31' THEN
                        INSERT INTO excel_import_errors (import_batch_id, row_number, column_name, error_type, error_message, raw_value)
                        VALUES (p_import_batch_id, p_row_number, v_field_name, 'validation', 
                               'Date must be between 2000-01-01 and 2030-12-31', v_value);
                        v_error_count := v_error_count + 1;
                    END IF;
                    -- Check future dates
                    IF v_date_value > CURRENT_DATE THEN
                        INSERT INTO excel_import_errors (import_batch_id, row_number, column_name, error_type, error_message, raw_value)
                        VALUES (p_import_batch_id, p_row_number, v_field_name, 'validation', 
                               'Mass celebration date cannot be in the future', v_value);
                        v_error_count := v_error_count + 1;
                    END IF;
                EXCEPTION
                    WHEN OTHERS THEN
                        INSERT INTO excel_import_errors (import_batch_id, row_number, column_name, error_type, error_message, raw_value)
                        VALUES (p_import_batch_id, p_row_number, v_field_name, 'format', 
                               'Invalid date format. Expected: YYYY-MM-DD', v_value);
                        v_error_count := v_error_count + 1;
                END;
                
            WHEN 'time' THEN
                BEGIN
                    v_time_value := v_value::TIME;
                EXCEPTION
                    WHEN OTHERS THEN
                        INSERT INTO excel_import_errors (import_batch_id, row_number, column_name, error_type, error_message, raw_value)
                        VALUES (p_import_batch_id, p_row_number, v_field_name, 'format', 
                               'Invalid time format. Expected: HH:MM:SS or HH:MM', v_value);
                        v_error_count := v_error_count + 1;
                END;
                
            WHEN 'number' THEN
                BEGIN
                    v_number_value := v_value::NUMERIC;
                    -- Validate attendees count
                    IF v_field_name = 'attendees_count' AND v_number_value < 0 THEN
                        INSERT INTO excel_import_errors (import_batch_id, row_number, column_name, error_type, error_message, raw_value)
                        VALUES (p_import_batch_id, p_row_number, v_field_name, 'validation', 
                               'Attendees count cannot be negative', v_value);
                        v_error_count := v_error_count + 1;
                    END IF;
                EXCEPTION
                    WHEN OTHERS THEN
                        INSERT INTO excel_import_errors (import_batch_id, row_number, column_name, error_type, error_message, raw_value)
                        VALUES (p_import_batch_id, p_row_number, v_field_name, 'format', 
                               'Invalid number format', v_value);
                        v_error_count := v_error_count + 1;
                END;
                
            WHEN 'text' THEN
                -- Validate text length
                IF LENGTH(v_value) > 255 AND v_field_name IN ('intention_title', 'location') THEN
                    INSERT INTO excel_import_errors (import_batch_id, row_number, column_name, error_type, error_message, raw_value)
                    VALUES (p_import_batch_id, p_row_number, v_field_name, 'validation', 
                           'Text too long. Maximum 255 characters allowed', v_value);
                    v_error_count := v_error_count + 1;
                END IF;
                
                -- Validate intention types
                IF v_field_name = 'intention_type' AND v_value NOT IN ('personal', 'special', 'anniversary', 'birthday', 'deceased') THEN
                    INSERT INTO excel_import_errors (import_batch_id, row_number, column_name, error_type, error_message, raw_value, suggested_value)
                    VALUES (p_import_batch_id, p_row_number, v_field_name, 'validation', 
                           'Invalid intention type', v_value, 'special');
                    v_error_count := v_error_count + 1;
                END IF;
                
                -- Validate sources
                IF v_field_name = 'source' AND v_value NOT IN ('personal', 'parish', 'individual', 'family', 'organization') THEN
                    INSERT INTO excel_import_errors (import_batch_id, row_number, column_name, error_type, error_message, raw_value, suggested_value)
                    VALUES (p_import_batch_id, p_row_number, v_field_name, 'validation', 
                           'Invalid source type', v_value, 'individual');
                    v_error_count := v_error_count + 1;
                END IF;
        END CASE;
    END LOOP;
    
    RETURN v_error_count = 0;
END;
$$ LANGUAGE plpgsql;

-- Create function to import Excel row data
CREATE OR REPLACE FUNCTION import_excel_mass_celebration(
    p_priest_id INTEGER,
    p_import_batch_id UUID,
    p_row_data JSONB,
    p_template_id INTEGER DEFAULT NULL
) RETURNS INTEGER AS $$
DECLARE
    v_template RECORD;
    v_celebration_id INTEGER;
    v_intention_id INTEGER;
    v_celebration_date DATE;
    v_mass_time TIME;
    v_intention_title TEXT;
    v_intention_description TEXT;
    v_intention_type TEXT := 'special';
    v_source TEXT := 'individual';
    v_location TEXT;
    v_notes TEXT;
    v_attendees_count INTEGER;
BEGIN
    -- Get template configuration
    IF p_template_id IS NOT NULL THEN
        SELECT * INTO v_template FROM excel_import_templates WHERE id = p_template_id;
    ELSE
        SELECT * INTO v_template FROM excel_import_templates WHERE template_name = 'Standard Mass Log';
    END IF;
    
    -- Extract values from row data based on template
    v_celebration_date := (p_row_data ->> (v_template.column_mappings -> 'celebration_date' ->> 'column'))::DATE;
    
    -- Extract optional fields
    IF v_template.column_mappings ? 'mass_time' THEN
        v_mass_time := (p_row_data ->> (v_template.column_mappings -> 'mass_time' ->> 'column'))::TIME;
    END IF;
    
    IF v_template.column_mappings ? 'intention_title' THEN
        v_intention_title := p_row_data ->> (v_template.column_mappings -> 'intention_title' ->> 'column');
    END IF;
    
    IF v_template.column_mappings ? 'intention_description' THEN
        v_intention_description := p_row_data ->> (v_template.column_mappings -> 'intention_description' ->> 'column');
    END IF;
    
    IF v_template.column_mappings ? 'intention_type' THEN
        v_intention_type := COALESCE(p_row_data ->> (v_template.column_mappings -> 'intention_type' ->> 'column'), 'special');
    END IF;
    
    IF v_template.column_mappings ? 'source' THEN
        v_source := COALESCE(p_row_data ->> (v_template.column_mappings -> 'source' ->> 'column'), 'individual');
    END IF;
    
    IF v_template.column_mappings ? 'location' THEN
        v_location := p_row_data ->> (v_template.column_mappings -> 'location' ->> 'column');
    END IF;
    
    IF v_template.column_mappings ? 'notes' THEN
        v_notes := p_row_data ->> (v_template.column_mappings -> 'notes' ->> 'column');
    END IF;
    
    IF v_template.column_mappings ? 'attendees_count' THEN
        v_attendees_count := (p_row_data ->> (v_template.column_mappings -> 'attendees_count' ->> 'column'))::INTEGER;
    END IF;
    
    -- Create mass intention if title is provided
    IF v_intention_title IS NOT NULL AND v_intention_title != '' THEN
        INSERT INTO mass_intentions (
            intention_type, title, description, source, created_by, assigned_to
        ) VALUES (
            v_intention_type, v_intention_title, v_intention_description, v_source, p_priest_id, p_priest_id
        ) RETURNING id INTO v_intention_id;
    END IF;
    
    -- Create mass celebration record
    INSERT INTO mass_celebrations (
        priest_id, celebration_date, intention_id, mass_time, location, 
        notes, attendees_count, imported_from_excel, import_batch_id
    ) VALUES (
        p_priest_id, v_celebration_date, v_intention_id, v_mass_time, v_location,
        v_notes, v_attendees_count, TRUE, p_import_batch_id
    ) RETURNING id INTO v_celebration_id;
    
    RETURN v_celebration_id;
END;
$$ LANGUAGE plpgsql;

-- Create function to process Excel import batch
CREATE OR REPLACE FUNCTION process_excel_import_batch(
    p_import_batch_id UUID,
    p_excel_data JSONB,  -- Array of row objects
    p_template_id INTEGER DEFAULT NULL
) RETURNS JSONB AS $$
DECLARE
    v_batch RECORD;
    v_row_data JSONB;
    v_row_number INTEGER := 1;
    v_successful_imports INTEGER := 0;
    v_failed_imports INTEGER := 0;
    v_celebration_id INTEGER;
    v_is_valid BOOLEAN;
    v_result JSONB;
BEGIN
    -- Get batch information
    SELECT * INTO v_batch FROM excel_import_batches WHERE uuid = p_import_batch_id;
    
    IF v_batch IS NULL THEN
        RAISE EXCEPTION 'Import batch not found';
    END IF;
    
    -- Update batch status to processing
    UPDATE excel_import_batches 
    SET status = 'processing', total_records = jsonb_array_length(p_excel_data)
    WHERE uuid = p_import_batch_id;
    
    -- Process each row
    FOR v_row_data IN SELECT * FROM jsonb_array_elements(p_excel_data)
    LOOP
        BEGIN
            -- Validate row data
            v_is_valid := validate_excel_import_row(p_import_batch_id, v_row_number, v_row_data, p_template_id);
            
            IF v_is_valid THEN
                -- Import the row
                v_celebration_id := import_excel_mass_celebration(v_batch.priest_id, p_import_batch_id, v_row_data, p_template_id);
                v_successful_imports := v_successful_imports + 1;
            ELSE
                v_failed_imports := v_failed_imports + 1;
            END IF;
            
        EXCEPTION
            WHEN OTHERS THEN
                -- Log unexpected errors
                INSERT INTO excel_import_errors (import_batch_id, row_number, error_type, error_message)
                VALUES (p_import_batch_id, v_row_number, 'business_rule', SQLERRM);
                v_failed_imports := v_failed_imports + 1;
        END;
        
        v_row_number := v_row_number + 1;
    END LOOP;
    
    -- Update batch with final results
    UPDATE excel_import_batches 
    SET 
        successful_imports = v_successful_imports,
        failed_imports = v_failed_imports,
        status = CASE 
            WHEN v_failed_imports = 0 THEN 'completed'
            WHEN v_successful_imports = 0 THEN 'failed'
            ELSE 'partial'
        END
    WHERE uuid = p_import_batch_id;
    
    -- Return summary
    v_result := jsonb_build_object(
        'batch_id', p_import_batch_id,
        'total_records', v_row_number - 1,
        'successful_imports', v_successful_imports,
        'failed_imports', v_failed_imports,
        'status', CASE 
            WHEN v_failed_imports = 0 THEN 'completed'
            WHEN v_successful_imports = 0 THEN 'failed'
            ELSE 'partial'
        END
    );
    
    RETURN v_result;
END;
$$ LANGUAGE plpgsql;

-- Create function to get import statistics
CREATE OR REPLACE FUNCTION get_import_statistics(
    p_priest_id INTEGER,
    p_year_start INTEGER DEFAULT NULL,
    p_year_end INTEGER DEFAULT NULL
) RETURNS JSONB AS $$
DECLARE
    v_stats JSONB;
    v_total_imports INTEGER;
    v_total_celebrations INTEGER;
    v_year_breakdown JSONB;
BEGIN
    -- Get overall statistics
    SELECT 
        COUNT(*) as total_batches,
        SUM(successful_imports) as total_successful,
        SUM(failed_imports) as total_failed,
        SUM(total_records) as total_records
    INTO v_total_imports, v_total_celebrations
    FROM excel_import_batches 
    WHERE priest_id = p_priest_id
    AND (p_year_start IS NULL OR year_range_start >= p_year_start)
    AND (p_year_end IS NULL OR year_range_end <= p_year_end);
    
    -- Get year breakdown
    SELECT jsonb_agg(
        jsonb_build_object(
            'year', celebration_year,
            'count', celebration_count
        )
    ) INTO v_year_breakdown
    FROM (
        SELECT 
            EXTRACT(YEAR FROM celebration_date) as celebration_year,
            COUNT(*) as celebration_count
        FROM mass_celebrations 
        WHERE priest_id = p_priest_id 
        AND imported_from_excel = TRUE
        AND (p_year_start IS NULL OR EXTRACT(YEAR FROM celebration_date) >= p_year_start)
        AND (p_year_end IS NULL OR EXTRACT(YEAR FROM celebration_date) <= p_year_end)
        GROUP BY EXTRACT(YEAR FROM celebration_date)
        ORDER BY celebration_year
    ) year_stats;
    
    -- Build result
    v_stats := jsonb_build_object(
        'priest_id', p_priest_id,
        'total_import_batches', v_total_imports,
        'total_imported_celebrations', v_total_celebrations,
        'year_breakdown', COALESCE(v_year_breakdown, '[]'::jsonb),
        'date_range', jsonb_build_object(
            'start_year', p_year_start,
            'end_year', p_year_end
        )
    );
    
    RETURN v_stats;
END;
$$ LANGUAGE plpgsql;

-- Create indexes for Excel import tables
CREATE INDEX idx_excel_import_errors_batch ON excel_import_errors(import_batch_id, row_number);
CREATE INDEX idx_excel_import_errors_type ON excel_import_errors(error_type, created_at DESC);
CREATE INDEX idx_excel_import_field_mappings_batch ON excel_import_field_mappings(import_batch_id);
CREATE INDEX idx_excel_import_templates_active ON excel_import_templates(template_name) WHERE is_active = TRUE;

-- Create view for import summary
CREATE VIEW excel_import_summary AS
SELECT 
    eib.*,
    u.full_name as priest_name,
    u.username as priest_username,
    (SELECT COUNT(*) FROM excel_import_errors WHERE import_batch_id = eib.uuid) as error_count,
    ROUND((eib.successful_imports::DECIMAL / NULLIF(eib.total_records, 0)) * 100, 2) as success_percentage
FROM excel_import_batches eib
JOIN users u ON eib.priest_id = u.id
ORDER BY eib.import_date DESC;

COMMENT ON TABLE excel_import_templates IS 'Templates defining how to map Excel columns to database fields';
COMMENT ON TABLE excel_import_errors IS 'Validation errors encountered during Excel import process';
COMMENT ON TABLE excel_import_field_mappings IS 'Field mapping configuration for each import batch';
COMMENT ON FUNCTION validate_excel_import_row IS 'Validates a single row of Excel data according to template rules';
COMMENT ON FUNCTION import_excel_mass_celebration IS 'Imports a single mass celebration record from Excel data';
COMMENT ON FUNCTION process_excel_import_batch IS 'Processes an entire Excel import batch with validation and error handling';
COMMENT ON FUNCTION get_import_statistics IS 'Returns import statistics for a priest within a date range';

