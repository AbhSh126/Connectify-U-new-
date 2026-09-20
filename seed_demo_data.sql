-- ============================================================
-- CONNECTIFYU DEMO SEED DATA
-- ============================================================
-- Run schema.sql first.
--
-- Demo password for all accounts:
-- Demo@12345
--
-- Passwords are stored as Argon2 hashes.
-- ============================================================


-- ============================================================
-- 1. DEMO USERS
-- ============================================================

INSERT INTO users
(email, password_hash, status)
VALUES
(
    'demo.student@connectifyu.com',
    '$argon2id$v=19$m=65536,t=3,p=4$pqB4P2sYUym+EbQq+qecFw$QeNXGz6RzNcmLUtfbHlj2M+bneL3GJyyK0CiYsK8MZs',
    'ACTIVE'
),
(
    'demo.organizer@connectifyu.com',
    '$argon2id$v=19$m=65536,t=3,p=4$pqB4P2sYUym+EbQq+qecFw$QeNXGz6RzNcmLUtfbHlj2M+bneL3GJyyK0CiYsK8MZs',
    'ACTIVE'
),
(
    'demo.admin@connectifyu.com',
    '$argon2id$v=19$m=65536,t=3,p=4$pqB4P2sYUym+EbQq+qecFw$QeNXGz6RzNcmLUtfbHlj2M+bneL3GJyyK0CiYsK8MZs',
    'ACTIVE'
)
ON CONFLICT (email) DO NOTHING;


-- ============================================================
-- 2. DEMO STUDENT
-- ============================================================

INSERT INTO students
(user_id, name, roll_no, branch, year)
SELECT
    user_id,
    'Demo Student',
    'DEMO-CSE-001',
    'Computer Science and Engineering',
    2
FROM users
WHERE email = 'demo.student@connectifyu.com'
ON CONFLICT (user_id) DO NOTHING;


-- ============================================================
-- 3. DEMO ORGANIZER REQUEST
-- ============================================================

INSERT INTO organizer_requests
(user_id, reason, organization, status, requested_at, reviewed_at)
SELECT
    user_id,
    'Demo organizer account for ConnectifyU testing',
    'ConnectifyU Demo Club',
    'APPROVED',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
FROM users
WHERE email = 'demo.organizer@connectifyu.com'
AND NOT EXISTS (
    SELECT 1
    FROM organizer_requests
    WHERE user_id = users.user_id
);


-- ============================================================
-- 4. DEMO ORGANIZER
-- ============================================================

INSERT INTO organizers
(user_id, organizer_type, organization, designation, status)
SELECT
    user_id,
    'STUDENT',
    'ConnectifyU Demo Club',
    'Student Organizer',
    'ACTIVE'
FROM users
WHERE email = 'demo.organizer@connectifyu.com'
ON CONFLICT (user_id) DO NOTHING;


-- ============================================================
-- 5. DEMO ADMIN
-- ============================================================

INSERT INTO admins
(user_id)
SELECT user_id
FROM users
WHERE email = 'demo.admin@connectifyu.com'
ON CONFLICT (user_id) DO NOTHING;


-- ============================================================
-- 6. DEMO SPEAKERS
-- ============================================================

INSERT INTO speakers
(name, designation, organization, bio)
VALUES
(
    'Dr. Demo Speaker',
    'Technology Researcher',
    'ConnectifyU Demo Labs',
    'Demo speaker for testing event details.'
),
(
    'Ms. Demo Trainer',
    'Software Engineer',
    'ConnectifyU Demo Labs',
    'Demo trainer for the coding workshop.'
);


-- ============================================================
-- 7. DEMO EVENTS
-- ============================================================

INSERT INTO events
(
    organizer_id,
    title,
    description,
    venue,
    event_date,
    event_time,
    duration_minutes,
    category,
    registration_deadline,
    status
)
SELECT
    o.organizer_id,
    'TechFest 2026',
    'Technology seminar for students.',
    'Seminar Hall',
    '2026-10-05',
    '10:00:00',
    240,
    'Technical',
    '2026-10-03 23:59:59',
    'PUBLISHED'
FROM organizers o
JOIN users u
    ON u.user_id = o.user_id
WHERE u.email = 'demo.organizer@connectifyu.com'
AND NOT EXISTS (
    SELECT 1
    FROM events
    WHERE title = 'TechFest 2026'
);


INSERT INTO events
(
    organizer_id,
    title,
    description,
    venue,
    event_date,
    event_time,
    duration_minutes,
    category,
    registration_deadline,
    status
)
SELECT
    o.organizer_id,
    'Coding Workshop',
    'Hands-on coding workshop for students.',
    'Computer Lab 2',
    '2026-10-15',
    '14:00:00',
    120,
    'Workshop',
    '2026-10-15 13:45:00',
    'PUBLISHED'
FROM organizers o
JOIN users u
    ON u.user_id = o.user_id
WHERE u.email = 'demo.organizer@connectifyu.com'
AND NOT EXISTS (
    SELECT 1
    FROM events
    WHERE title = 'Coding Workshop'
);


-- ============================================================
-- 8. CONNECT SPEAKERS TO EVENTS
-- ============================================================

INSERT INTO event_speakers
(event_id, speaker_id)
SELECT
    e.event_id,
    s.speaker_id
FROM events e
CROSS JOIN speakers s
WHERE e.title = 'TechFest 2026'
AND s.name = 'Dr. Demo Speaker'
ON CONFLICT DO NOTHING;


INSERT INTO event_speakers
(event_id, speaker_id)
SELECT
    e.event_id,
    s.speaker_id
FROM events e
CROSS JOIN speakers s
WHERE e.title = 'Coding Workshop'
AND s.name = 'Ms. Demo Trainer'
ON CONFLICT DO NOTHING;


-- ============================================================
-- 9. DEMO STUDENT REGISTRATION
-- ============================================================

INSERT INTO registrations
(student_id, event_id, registered_at, status)
SELECT
    st.student_id,
    e.event_id,
    CURRENT_TIMESTAMP,
    'REGISTERED'
FROM students st
JOIN users u
    ON u.user_id = st.user_id
CROSS JOIN events e
WHERE u.email = 'demo.student@connectifyu.com'
AND e.title = 'TechFest 2026'
ON CONFLICT (student_id, event_id) DO NOTHING;
