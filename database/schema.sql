
-- CONNECTIFYU DATABASE SCHEMA


-- 1. USERS
CREATE TABLE users (
    user_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE'
        CHECK (status IN ('ACTIVE', 'INACTIVE'))
);


-- 2. STUDENTS
CREATE TABLE students (
    student_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    roll_no VARCHAR(50) NOT NULL UNIQUE,
    branch VARCHAR(100) NOT NULL,
    year INTEGER NOT NULL
        CHECK (year BETWEEN 1 AND 4),

    CONSTRAINT fk_student_user
        FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE
);


-- 3. ORGANIZERS
CREATE TABLE organizers (
    organizer_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE,
    organizer_type VARCHAR(20) NOT NULL
        CHECK (organizer_type IN ('STUDENT', 'FACULTY', 'EXTERNAL')),
    organization VARCHAR(150),
    designation VARCHAR(100),

    CONSTRAINT fk_organizer_user
        FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE
);


-- 4. ADMINS
CREATE TABLE admins (
    admin_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE,

    CONSTRAINT fk_admin_user
        FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE
);


-- 5. EVENTS
CREATE TABLE events (
    event_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organizer_id INTEGER NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    venue VARCHAR(200) NOT NULL,
    event_date DATE NOT NULL,
    event_time TIME NOT NULL,
    duration_minutes INTEGER NOT NULL
        CHECK (duration_minutes > 0),
    category VARCHAR(100) NOT NULL,
    registration_deadline TIMESTAMP NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PUBLISHED'
        CHECK (status IN ('DRAFT', 'PUBLISHED', 'CANCELLED', 'COMPLETED')),

    CONSTRAINT fk_event_organizer
        FOREIGN KEY (organizer_id)
        REFERENCES organizers(organizer_id)
        ON DELETE RESTRICT
);


-- 6. SPEAKERS
CREATE TABLE speakers (
    speaker_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    designation VARCHAR(100),
    organization VARCHAR(150),
    bio TEXT
);


-- 7. EVENT_SPEAKERS
-- Junction table for Event <-> Speaker many-to-many relationship
CREATE TABLE event_speakers (
    event_id INTEGER NOT NULL,
    speaker_id INTEGER NOT NULL,

    PRIMARY KEY (event_id, speaker_id),

    CONSTRAINT fk_event_speaker_event
        FOREIGN KEY (event_id)
        REFERENCES events(event_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_event_speaker_speaker
        FOREIGN KEY (speaker_id)
        REFERENCES speakers(speaker_id)
        ON DELETE CASCADE
);


-- 8. REGISTRATIONS
CREATE TABLE registrations (
    registration_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    student_id INTEGER NOT NULL,
    event_id INTEGER NOT NULL,
    registered_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) NOT NULL DEFAULT 'REGISTERED'
        CHECK (status IN ('REGISTERED', 'CANCELLED')),

    CONSTRAINT fk_registration_student
        FOREIGN KEY (student_id)
        REFERENCES students(student_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_registration_event
        FOREIGN KEY (event_id)
        REFERENCES events(event_id)
        ON DELETE CASCADE,

    CONSTRAINT unique_student_event
        UNIQUE (student_id, event_id)
);

CREATE TABLE password_reset_tokens (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_password_reset_user
        FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE
);