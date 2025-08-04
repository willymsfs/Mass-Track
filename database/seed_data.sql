-- Mass Tracking System Seed Data
-- Author: Manus AI
-- Date: January 8, 2025
-- Description: Sample data for testing and development

-- Insert sample users (priests)
INSERT INTO users (username, email, password_hash, full_name, ordination_date, current_assignment, diocese, province, phone, address) VALUES
('father.john', 'father.john@diocese.org', crypt('password123', gen_salt('bf')), 'Father John Smith', '2010-05-15', 'St. Mary Parish', 'Diocese of Springfield', 'Eastern Province', '+1-555-0101', '123 Church Street, Springfield, IL'),
('father.michael', 'father.michael@diocese.org', crypt('password123', gen_salt('bf')), 'Father Michael Johnson', '2008-06-20', 'Sacred Heart Church', 'Diocese of Springfield', 'Eastern Province', '+1-555-0102', '456 Faith Avenue, Springfield, IL'),
('father.david', 'father.david@diocese.org', crypt('password123', gen_salt('bf')), 'Father David Wilson', '2015-04-10', 'St. Joseph Cathedral', 'Diocese of Springfield', 'Western Province', '+1-555-0103', '789 Hope Boulevard, Springfield, IL'),
('father.thomas', 'father.thomas@diocese.org', crypt('password123', gen_salt('bf')), 'Father Thomas Brown', '2012-08-25', 'Our Lady of Peace', 'Diocese of Springfield', 'Eastern Province', '+1-555-0104', '321 Grace Lane, Springfield, IL'),
('father.robert', 'father.robert@diocese.org', crypt('password123', gen_salt('bf')), 'Father Robert Davis', '2005-03-12', 'St. Francis Church', 'Diocese of Springfield', 'Central Province', '+1-555-0105', '654 Mercy Street, Springfield, IL');

-- Insert sample mass intentions
INSERT INTO mass_intentions (intention_type, title, description, source, source_contact, created_by, assigned_to, priority, is_fixed_date, fixed_date) VALUES
-- Personal intentions
('personal', 'Personal Monthly Mass #1', 'First personal mass intention for the month', 'personal', '{}', 1, 1, 1, FALSE, NULL),
('personal', 'Personal Monthly Mass #2', 'Second personal mass intention for the month', 'personal', '{}', 1, 1, 1, FALSE, NULL),
('personal', 'Personal Monthly Mass #3', 'Third personal mass intention for the month', 'personal', '{}', 1, 1, 1, FALSE, NULL),

-- Bulk intentions from province
('bulk', 'Province Intentions - January 2025', 'Monthly bulk intentions from Eastern Province', 'province', '{"contact_person": "Provincial Superior", "email": "provincial@easternprovince.org"}', 1, 1, 2, FALSE, NULL),
('bulk', 'Generalate Intentions - Q1 2025', 'Quarterly bulk intentions from Generalate', 'generalate', '{"contact_person": "General Superior", "email": "general@congregation.org"}', 1, 2, 2, FALSE, NULL),

-- Fixed date intentions
('fixed_date', 'Memorial Mass for Fr. Anthony', 'Annual memorial mass for deceased priest', 'province', '{"contact_person": "Memorial Committee"}', 1, 1, 3, TRUE, '2025-02-15'),
('fixed_date', 'Founder Day Celebration', 'Mass for congregation founder anniversary', 'generalate', '{"contact_person": "Generalate Office"}', 1, 3, 3, TRUE, '2025-03-19'),

-- Special occasions
('special', 'Golden Jubilee Mass', 'Mass for priest 50th ordination anniversary', 'parish', '{"contact_person": "Parish Council", "phone": "+1-555-0201"}', 1, 2, 2, FALSE, NULL),
('anniversary', 'Wedding Anniversary Mass', 'Mass for couple 25th wedding anniversary', 'individual', '{"contact_person": "John and Mary Doe", "phone": "+1-555-0301"}', 1, 1, 1, FALSE, NULL),
('birthday', 'Birthday Thanksgiving Mass', 'Mass for birthday thanksgiving', 'family', '{"contact_person": "Smith Family", "phone": "+1-555-0401"}', 1, 4, 1, FALSE, NULL),
('deceased', 'Memorial Mass for Maria Santos', 'One month memorial mass', 'family', '{"contact_person": "Santos Family", "phone": "+1-555-0501"}', 1, 5, 2, FALSE, NULL);

-- Insert bulk intentions with countdown logic
INSERT INTO bulk_intentions (intention_id, priest_id, total_count, current_count, start_date, estimated_end_date) VALUES
(4, 1, 50, 47, '2025-01-01', '2025-02-19'),  -- Father John has 47 remaining out of 50
(5, 2, 100, 95, '2025-01-01', '2025-04-10'); -- Father Michael has 95 remaining out of 100

-- Insert sample mass celebrations for the current month
INSERT INTO mass_celebrations (priest_id, celebration_date, intention_id, bulk_intention_id, serial_number, mass_time, location, notes, attendees_count) VALUES
-- Father John's celebrations
(1, '2025-01-01', 4, 1, 50, '07:00:00', 'St. Mary Parish', 'New Year Day Mass', 120),
(1, '2025-01-02', 4, 1, 49, '07:00:00', 'St. Mary Parish', 'Morning Mass', 45),
(1, '2025-01-03', 4, 1, 48, '07:00:00', 'St. Mary Parish', 'Daily Mass', 35),
(1, '2025-01-05', 1, NULL, NULL, '07:00:00', 'St. Mary Parish', 'Personal intention mass', 40),
(1, '2025-01-06', 6, NULL, NULL, '10:00:00', 'St. Mary Parish', 'Memorial Mass for Fr. Anthony (early celebration)', 80),
(1, '2025-01-07', 9, NULL, NULL, '07:00:00', 'St. Mary Parish', 'Anniversary Mass', 25),

-- Father Michael's celebrations  
(2, '2025-01-01', 5, 2, 100, '08:00:00', 'Sacred Heart Church', 'New Year Day Mass', 150),
(2, '2025-01-02', 5, 2, 99, '08:00:00', 'Sacred Heart Church', 'Morning Mass', 55),
(2, '2025-01-03', 5, 2, 98, '08:00:00', 'Sacred Heart Church', 'Daily Mass', 42),
(2, '2025-01-04', 5, 2, 97, '08:00:00', 'Sacred Heart Church', 'Daily Mass', 38),
(2, '2025-01-05', 5, 2, 96, '08:00:00', 'Sacred Heart Church', 'Daily Mass', 41),
(2, '2025-01-06', 5, 2, 95, '08:00:00', 'Sacred Heart Church', 'Daily Mass', 39),

-- Father David's celebrations
(3, '2025-01-01', NULL, NULL, NULL, '09:00:00', 'St. Joseph Cathedral', 'New Year Day Mass', 200),
(3, '2025-01-02', NULL, NULL, NULL, '09:00:00', 'St. Joseph Cathedral', 'Daily Mass', 75),
(3, '2025-01-03', NULL, NULL, NULL, '09:00:00', 'St. Joseph Cathedral', 'Daily Mass', 68),

-- Father Thomas's celebrations
(4, '2025-01-01', 10, NULL, NULL, '07:30:00', 'Our Lady of Peace', 'Birthday Mass', 30),
(4, '2025-01-02', NULL, NULL, NULL, '07:30:00', 'Our Lady of Peace', 'Daily Mass', 28),
(4, '2025-01-03', NULL, NULL, NULL, '07:30:00', 'Our Lady of Peace', 'Daily Mass', 32),

-- Father Robert's celebrations
(5, '2025-01-01', 11, NULL, NULL, '08:30:00', 'St. Francis Church', 'Memorial Mass', 45),
(5, '2025-01-02', NULL, NULL, NULL, '08:30:00', 'St. Francis Church', 'Daily Mass', 35),
(5, '2025-01-03', NULL, NULL, NULL, '08:30:00', 'St. Francis Church', 'Daily Mass', 38);

-- Insert monthly obligations for current month
INSERT INTO monthly_obligations (priest_id, year, month, completed_count, target_count) VALUES
(1, 2025, 1, 1, 3),  -- Father John completed 1 out of 3
(2, 2025, 1, 0, 3),  -- Father Michael completed 0 out of 3
(3, 2025, 1, 0, 3),  -- Father David completed 0 out of 3
(4, 2025, 1, 0, 3),  -- Father Thomas completed 0 out of 3
(5, 2025, 1, 0, 3);  -- Father Robert completed 0 out of 3

-- Link personal mass celebrations to monthly obligations
INSERT INTO personal_mass_celebrations (monthly_obligation_id, mass_celebration_id) VALUES
(1, 4);  -- Father John's personal mass on Jan 5th

-- Insert special occasions for recurring events
INSERT INTO special_occasions (priest_id, occasion_type, title, description, recurring_date, is_recurring, priority) VALUES
(1, 'ordination_anniversary', 'Ordination Anniversary', 'Annual celebration of ordination', '2025-05-15', TRUE, 3),
(2, 'ordination_anniversary', 'Ordination Anniversary', 'Annual celebration of ordination', '2025-06-20', TRUE, 3),
(3, 'ordination_anniversary', 'Ordination Anniversary', 'Annual celebration of ordination', '2025-04-10', TRUE, 3),
(4, 'ordination_anniversary', 'Ordination Anniversary', 'Annual celebration of ordination', '2025-08-25', TRUE, 3),
(5, 'ordination_anniversary', 'Ordination Anniversary', 'Annual celebration of ordination', '2025-03-12', TRUE, 3),

-- Some birthday celebrations for parishioners
(1, 'birthday', 'Parish Council President Birthday', 'Annual birthday mass for council president', '2025-02-28', TRUE, 1),
(2, 'birthday', 'Church Organist Birthday', 'Annual birthday mass for organist', '2025-03-15', TRUE, 1),
(3, 'death_anniversary', 'Former Pastor Memorial', 'Annual memorial for former pastor', '2025-04-22', TRUE, 2);

-- Insert some notifications for testing
INSERT INTO notifications (priest_id, notification_type, title, message, priority, scheduled_for) VALUES
(1, 'reminder', 'Monthly Personal Masses', 'You have completed 1 out of 3 personal masses for January 2025. Remember to complete the remaining 2 before month end.', 'normal', NOW() + INTERVAL '1 day'),
(1, 'warning', 'Bulk Intention Low Count', 'Your bulk intention "Province Intentions - January 2025" has only 47 masses remaining. Consider planning your celebration schedule.', 'high', NOW()),
(2, 'info', 'New Bulk Intention Assigned', 'You have been assigned a new bulk intention: "Generalate Intentions - Q1 2025" with 100 masses.', 'normal', NOW() - INTERVAL '1 hour'),
(1, 'reminder', 'Fixed Date Mass Approaching', 'Memorial Mass for Fr. Anthony is scheduled for February 15, 2025. Please prepare accordingly.', 'high', '2025-02-10 09:00:00'),
(3, 'info', 'Welcome to Mass Tracking System', 'Welcome to the Mass Tracking System. Please update your profile and start recording your daily masses.', 'normal', NOW() - INTERVAL '2 days');

-- Insert pause events for bulk intentions (showing history)
INSERT INTO pause_events (bulk_intention_id, event_type, event_date, reason, count_at_event, notes) VALUES
(1, 'pause', '2025-01-04', 'Fixed date mass for memorial', 48, 'Paused for Fr. Anthony memorial mass preparation'),
(1, 'resume', '2025-01-07', NULL, 48, 'Resumed after memorial mass celebration');

-- Insert sample Excel import batch (simulating historical data import)
INSERT INTO excel_import_batches (priest_id, filename, total_records, successful_imports, failed_imports, year_range_start, year_range_end, status) VALUES
(1, 'father_john_masses_2020_2024.xlsx', 1825, 1820, 5, 2020, 2024, 'completed'),
(2, 'father_michael_masses_2015_2019.xlsx', 1460, 1455, 5, 2015, 2019, 'completed');

-- Insert some historical mass celebrations (simulating imported data)
INSERT INTO mass_celebrations (priest_id, celebration_date, intention_id, mass_time, location, notes, imported_from_excel, import_batch_id) VALUES
-- Sample historical data for Father John (2024)
(1, '2024-12-25', NULL, '00:00:00', 'St. Mary Parish', 'Christmas Midnight Mass', TRUE, (SELECT uuid FROM excel_import_batches WHERE id = 1)),
(1, '2024-12-25', NULL, '10:00:00', 'St. Mary Parish', 'Christmas Morning Mass', TRUE, (SELECT uuid FROM excel_import_batches WHERE id = 1)),
(1, '2024-12-24', NULL, '18:00:00', 'St. Mary Parish', 'Christmas Eve Mass', TRUE, (SELECT uuid FROM excel_import_batches WHERE id = 1)),
(1, '2024-12-31', NULL, '23:00:00', 'St. Mary Parish', 'New Year Eve Mass', TRUE, (SELECT uuid FROM excel_import_batches WHERE id = 1)),

-- Sample historical data for Father Michael (2019)
(2, '2019-12-25', NULL, '00:00:00', 'Sacred Heart Church', 'Christmas Midnight Mass', TRUE, (SELECT uuid FROM excel_import_batches WHERE id = 2)),
(2, '2019-12-25', NULL, '10:00:00', 'Sacred Heart Church', 'Christmas Morning Mass', TRUE, (SELECT uuid FROM excel_import_batches WHERE id = 2)),
(2, '2019-12-24', NULL, '18:00:00', 'Sacred Heart Church', 'Christmas Eve Mass', TRUE, (SELECT uuid FROM excel_import_batches WHERE id = 2)),
(2, '2019-12-31', NULL, '23:00:00', 'Sacred Heart Church', 'New Year Eve Mass', TRUE, (SELECT uuid FROM excel_import_batches WHERE id = 2));

-- Insert audit log entries for recent activities
INSERT INTO audit_log (user_id, action, entity_type, entity_id, new_values, ip_address, user_agent) VALUES
(1, 'login', 'users', 1, '{"login_time": "2025-01-08T10:00:00Z"}', '192.168.1.100', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'),
(1, 'create', 'mass_celebrations', 4, '{"celebration_date": "2025-01-05", "intention_type": "personal"}', '192.168.1.100', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'),
(2, 'login', 'users', 2, '{"login_time": "2025-01-08T08:30:00Z"}', '192.168.1.101', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'),
(1, 'update', 'bulk_intentions', 1, '{"current_count": 47, "completed_count": 3}', '192.168.1.100', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'),
(3, 'login', 'users', 3, '{"login_time": "2025-01-08T09:15:00Z"}', '192.168.1.102', 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15');

-- Update last login times for users
UPDATE users SET last_login = NOW() - INTERVAL '2 hours' WHERE id = 1;
UPDATE users SET last_login = NOW() - INTERVAL '4 hours' WHERE id = 2;
UPDATE users SET last_login = NOW() - INTERVAL '1 hour' WHERE id = 3;
UPDATE users SET last_login = NOW() - INTERVAL '6 hours' WHERE id = 4;
UPDATE users SET last_login = NOW() - INTERVAL '8 hours' WHERE id = 5;

-- Update bulk intentions completed counts based on celebrations
UPDATE bulk_intentions SET completed_count = 3 WHERE id = 1;  -- Father John completed 3 masses
UPDATE bulk_intentions SET completed_count = 5 WHERE id = 2;  -- Father Michael completed 5 masses

COMMENT ON TABLE users IS 'Sample priest users for testing the mass tracking system';
COMMENT ON TABLE mass_celebrations IS 'Sample mass celebration records showing different intention types';
COMMENT ON TABLE bulk_intentions IS 'Sample bulk intentions with countdown logic demonstration';
COMMENT ON TABLE monthly_obligations IS 'Sample monthly personal mass tracking';
COMMENT ON TABLE notifications IS 'Sample system notifications and reminders';
COMMENT ON TABLE excel_import_batches IS 'Sample Excel import records for historical data';
COMMENT ON TABLE audit_log IS 'Sample audit trail for system activities';

