-- ConnectifyU demo seed data
-- Run schema.sql first.
-- No passwords or JWT tokens are stored here.
-- Create accounts through /signup so the application performs password hashing.

INSERT INTO events
(organizer_id, title, description, venue, event_date, event_time,
 duration_minutes, category, registration_deadline, status)
VALUES
(1, 'TechFest 2026', 'Technology seminar for students.', 'Seminar Hall',
 '2026-10-05', '10:00:00', 240, 'Technical',
 '2026-10-03 23:59:59', 'PUBLISHED')
ON CONFLICT DO NOTHING;

INSERT INTO events
(organizer_id, title, description, venue, event_date, event_time,
 duration_minutes, category, registration_deadline, status)
VALUES
(1, 'Coding Workshop', 'Hands-on coding workshop.', 'Computer Lab 2',
 '2026-10-15', '14:00:00', 120, 'Workshop',
 '2026-10-15 13:45:00', 'PUBLISHED')
ON CONFLICT DO NOTHING;
