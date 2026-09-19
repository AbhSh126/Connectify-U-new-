#main work is handling request

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from backend.database import get_connection
from datetime import datetime, timedelta
from pwdlib import PasswordHash
import jwt
import os
import secrets
import hashlib
from dotenv import load_dotenv

load_dotenv()


app = FastAPI() #Main object

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

password_hash = PasswordHash.recommended()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        return payload

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

def get_current_student(
    current_user = Depends(get_current_user)
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT student_id
        FROM students
        WHERE user_id = %s;
    """, (current_user["user_id"],))

    student = cursor.fetchone()

    cursor.close()
    connection.close()

    if student is None:
        raise HTTPException(
            status_code=403,
            detail="Student profile not found"
        )

    return student[0]

@app.get("/student-id-test")
def student_id_test(
    student_id = Depends(get_current_student)
):
    return {
        "message": "Student identity verified",
        "student_id": student_id
    }


def require_organizer(
    current_user = Depends(get_current_user)
):
    if "organizer" not in current_user["roles"]:
        raise HTTPException(
            status_code=403,
            detail="Organizer access required"
        )

    return current_user

def require_admin(
    current_user = Depends(get_current_user)
):
    if "admin" not in current_user["roles"]:
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )

    return current_user


@app.get("/admin/organizer-requests")
def get_organizer_requests(
    current_user = Depends(require_admin)
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            request_id,
            user_id,
            reason,
            organization,
            status,
            requested_at,
            reviewed_at
        FROM organizer_requests
        WHERE status = 'PENDING'
        ORDER BY requested_at;
    """)

    requests = cursor.fetchall()

    cursor.close()
    connection.close()

    result = []

    for request in requests:
        result.append({
            "request_id": request[0],
            "user_id": request[1],
            "reason": request[2],
            "organization": request[3],
            "status": request[4],
            "requested_at": str(request[5]),
            "reviewed_at": str(request[6]) if request[6] else None
        })

    return {
        "total_pending_requests": len(result),
        "requests": result
    }

@app.post("/admin/organizer-requests/{request_id}/approve")
def approve_organizer_request(
    request_id: int,
    current_user = Depends(require_admin)
):

    connection = get_connection()
    cursor = connection.cursor()

    # Find the organizer request
    cursor.execute("""
        SELECT
            request_id,
            user_id,
            organization,
            status
        FROM organizer_requests
        WHERE request_id = %s;
    """, (request_id,))

    request = cursor.fetchone()

    if request is None:
        cursor.close()
        connection.close()

        raise HTTPException(
            status_code=404,
            detail="Organizer request not found"
        )

    request_user_id = request[1]
    organization = request[2]
    request_status = request[3]

    # Request must still be pending
    if request_status != "PENDING":
        cursor.close()
        connection.close()

        raise HTTPException(
            status_code=400,
            detail="This request has already been reviewed"
        )

    # Check whether user is already an organizer
    cursor.execute("""
        SELECT organizer_id
        FROM organizers
        WHERE user_id = %s;
    """, (request_user_id,))

    existing_organizer = cursor.fetchone()

    if existing_organizer is not None:
        cursor.close()
        connection.close()

        raise HTTPException(
            status_code=400,
            detail="User is already an organizer"
        )

    # Create organizer profile
    cursor.execute("""
        INSERT INTO organizers
        (
            user_id,
            organizer_type,
            organization,
            designation
        )
        VALUES
        (
            %s,
            'STUDENT',
            %s,
            'Student Organizer'
        )
        RETURNING organizer_id;
    """, (
        request_user_id,
        organization
    ))

    organizer_id = cursor.fetchone()[0]

    # Update request status
    cursor.execute("""
        UPDATE organizer_requests
        SET
            status = 'APPROVED',
            reviewed_at = CURRENT_TIMESTAMP
        WHERE request_id = %s;
    """, (request_id,))

    connection.commit()

    cursor.close()
    connection.close()

    return {
        "message": "Organizer request approved successfully",
        "request_id": request_id,
        "user_id": request_user_id,
        "organizer_id": organizer_id,
        "status": "APPROVED"
    }

@app.post("/admin/organizer-requests/{request_id}/reject")
def reject_organizer_request(
    request_id: int,
    current_user = Depends(require_admin)
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            request_id,
            status
        FROM organizer_requests
        WHERE request_id = %s;
    """, (request_id,))

    request = cursor.fetchone()

    if request is None:
        cursor.close()
        connection.close()
        raise HTTPException(
            status_code=404,
            detail="Organizer request not found"
        )

    request_status = request[1]

    if request_status != "PENDING":
        cursor.close()
        connection.close()
        raise HTTPException(
            status_code=400,
            detail="This request has already been reviewed"
        )

    cursor.execute("""
        UPDATE organizer_requests
        SET
            status = 'REJECTED',
            reviewed_at = CURRENT_TIMESTAMP
        WHERE request_id = %s;
    """, (request_id,))

    connection.commit()

    cursor.close()
    connection.close()

    return {
        "message": "Organizer request rejected successfully",
        "request_id": request_id,
        "status": "REJECTED"
    }

def get_current_organizer(
    current_user = Depends(require_organizer)
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT organizer_id
        FROM organizers
        WHERE user_id = %s;
    """, (current_user["user_id"],))

    organizer = cursor.fetchone()

    cursor.close()
    connection.close()

    if organizer is None:
        raise HTTPException(
            status_code=403,
            detail="Organizer profile not found"
        )

    return organizer[0]

@app.get("/organizer-id-test")
def organizer_id_test(
    organizer_id = Depends(get_current_organizer)
):
    return {
        "message": "Organizer identity verified",
        "organizer_id": organizer_id
    }

@app.get("/event-owner-test/{event_id}")
def event_owner_test(
    event_id: int,
    organizer_id = Depends(get_current_organizer)
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT organizer_id
        FROM events
        WHERE event_id = %s;
    """, (event_id,))

    event = cursor.fetchone()

    cursor.close()
    connection.close()

    if event is None:
        raise HTTPException(
            status_code=404,
            detail="Event not found"
        )

    if event[0] != organizer_id:
        raise HTTPException(
            status_code=403,
            detail="You do not own this event"
        )

    return {
        "message": "Event ownership verified",
        "event_id": event_id,
        "organizer_id": organizer_id
    }

@app.get("/protected")
def protected_route(current_user = Depends(get_current_user)):
    return {
        "message": "You are authenticated",
        "user": current_user
    }

@app.get("/organizer-test")
def organizer_test(
    current_user = Depends(require_organizer)
):
    return {
        "message": "Organizer access granted",
        "user": current_user
    }


@app.get("/")
def home():
    return {
        "message": "ConnectifyU Backend is running"
    }


@app.get("/test-db")
def test_database():
    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("SELECT 1;")

    result = cursor.fetchone()

    cursor.close()
    connection.close()

    return {
        "database": "connected",
        "result": result[0]
    }

@app.get("/events")
def get_events():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            event_id,
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
        FROM events
        ORDER BY event_date, event_time;
    """)

    events = cursor.fetchall()

    cursor.close()
    connection.close()

    result = []

    for event in events:
        result.append({
            "event_id": event[0],
            "organizer_id": event[1],
            "title": event[2],
            "description": event[3],
            "venue": event[4],
            "event_date": str(event[5]),
            "event_time": str(event[6]),
            "duration_minutes": event[7],
            "category": event[8],
            "registration_deadline": str(event[9]),
            "status": event[10]
        })

    return result

@app.get("/events/{event_id}")
def get_event(event_id: int):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            event_id,
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
        FROM events
        WHERE event_id = %s;
    """, (event_id,))

    event = cursor.fetchone()

    cursor.close()
    connection.close()

    if event is None:
        return {
            "error": "Event not found"
        }

    return {
        "event_id": event[0],
        "organizer_id": event[1],
        "title": event[2],
        "description": event[3],
        "venue": event[4],
        "event_date": str(event[5]),
        "event_time": str(event[6]),
        "duration_minutes": event[7],
        "category": event[8],
        "registration_deadline": str(event[9]),
        "status": event[10]
    }

@app.post("/registrations")
def register_student(
    event_id: int,
    student_id = Depends(get_current_student)
):

    connection = get_connection()
    cursor = connection.cursor()

    # Check whether event exists
    # Also get its organizer, status and registration deadline
    cursor.execute("""
        SELECT
            event_id,
            organizer_id,
            status,
            registration_deadline
        FROM events
        WHERE event_id = %s;
    """, (event_id,))

    event = cursor.fetchone()

    if event is None:
        cursor.close()
        connection.close()

        raise HTTPException(
            status_code=404,
            detail="Event not found"
        )

    event_organizer_id = event[1]
    event_status = event[2]
    registration_deadline = event[3]

    # Check whether the student is the organizer of this event
    cursor.execute("""
        SELECT organizer_id
        FROM organizers
        WHERE user_id = (
            SELECT user_id
            FROM students
            WHERE student_id = %s
        );
    """, (student_id,))

    organizer = cursor.fetchone()

    if organizer is not None and organizer[0] == event_organizer_id:
        cursor.close()
        connection.close()

        raise HTTPException(
            status_code=403,
            detail="Organizers cannot register for their own event"
        )

    # Only published events can accept registrations
    if event_status != "PUBLISHED":
        cursor.close()
        connection.close()

        return {
            "error": "Registration is not available for this event",
            "event_id": event_id,
            "status": event_status
        }

    # Check whether registration deadline has passed
    current_time = datetime.now()

    if registration_deadline is not None and current_time > registration_deadline:
        cursor.close()
        connection.close()

        return {
            "error": "Registration deadline has passed",
            "event_id": event_id,
            "registration_deadline": str(registration_deadline)
        }

    # Check whether student is already registered
    cursor.execute("""
        SELECT registration_id
        FROM registrations
        WHERE student_id = %s
        AND event_id = %s;
    """, (student_id, event_id))

    existing_registration = cursor.fetchone()

    if existing_registration is not None:
        cursor.close()
        connection.close()

        return {
            "error": "Student is already registered for this event"
        }

    # Register student
    cursor.execute("""
        INSERT INTO registrations
        (
            student_id,
            event_id
        )
        VALUES
        (
            %s,
            %s
        )
        RETURNING registration_id;
    """, (student_id, event_id))

    registration_id = cursor.fetchone()[0]

    connection.commit()

    cursor.close()
    connection.close()

    return {
        "message": "Registration successful",
        "registration_id": registration_id,
        "student_id": student_id,
        "event_id": event_id
    }

@app.get("/students/me/registrations")
def get_my_registrations(
    student_id = Depends(get_current_student)
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            r.registration_id,
            r.event_id,
            e.title,
            e.description,
            e.category,
            e.venue,
            e.event_date,
            e.event_time,
            e.duration_minutes,
            r.registered_at,
            r.status
        FROM registrations r
        JOIN events e
            ON r.event_id = e.event_id
        WHERE r.student_id = %s
        ORDER BY e.event_date, e.event_time;
    """, (student_id,))

    registrations = cursor.fetchall()

    cursor.close()
    connection.close()

    registered_events = []
    cancelled_registrations = []

    for registration in registrations:

        event_data = {
            "registration_id": registration[0],
            "event_id": registration[1],
            "title": registration[2],
            "description": registration[3],
            "category": registration[4],
            "venue": registration[5],
            "event_date": str(registration[6]),
            "event_time": str(registration[7]),
            "duration_minutes": registration[8],
            "registered_at": str(registration[9]),
            "status": registration[10]
        }

        if registration[10] == "REGISTERED":
            registered_events.append(event_data)

        elif registration[10] == "CANCELLED":
            cancelled_registrations.append(event_data)

    return {
        "registered_events": {
            "total": len(registered_events),
            "events": registered_events
        },

        "cancelled_registrations": {
            "total": len(cancelled_registrations),
            "events": cancelled_registrations
        }
    }

@app.delete("/registrations/{registration_id}")
def cancel_registration(
    registration_id: int,
    student_id = Depends(get_current_student)
):

    connection = get_connection()
    cursor = connection.cursor()

    # Check whether this registration belongs to the logged-in student
    cursor.execute("""
        SELECT
            registration_id,
            event_id,
            status
        FROM registrations
        WHERE registration_id = %s
        AND student_id = %s;
    """, (registration_id, student_id))

    registration = cursor.fetchone()

    if registration is None:
        cursor.close()
        connection.close()

        raise HTTPException(
            status_code=404,
            detail="Registration not found"
        )

    current_status = registration[2]

    # Check whether registration is already cancelled
    if current_status == "CANCELLED":
        cursor.close()
        connection.close()

        return {
            "error": "Registration is already cancelled",
            "registration_id": registration_id
        }

    # Cancel registration
    cursor.execute("""
        UPDATE registrations
        SET status = 'CANCELLED'
        WHERE registration_id = %s
        AND student_id = %s;
    """, (registration_id, student_id))

    connection.commit()

    cursor.close()
    connection.close()

    return {
        "message": "Registration cancelled successfully",
        "registration_id": registration_id,
        "status": "CANCELLED"
    }

@app.post("/organizer-requests")
def create_organizer_request(
    reason: str,
    organization: str,
    current_user = Depends(get_current_user)
):

    user_id = current_user["user_id"]

    connection = get_connection()
    cursor = connection.cursor()

    # Check whether the user already has an organizer profile
    cursor.execute("""
        SELECT organizer_id
        FROM organizers
        WHERE user_id = %s;
    """, (user_id,))

    organizer = cursor.fetchone()

    if organizer is not None:
        cursor.close()
        connection.close()

        raise HTTPException(
            status_code=400,
            detail="You are already an organizer"
        )

    # Check whether a pending request already exists
    cursor.execute("""
        SELECT request_id
        FROM organizer_requests
        WHERE user_id = %s
        AND status = 'PENDING';
    """, (user_id,))

    existing_request = cursor.fetchone()

    if existing_request is not None:
        cursor.close()
        connection.close()

        raise HTTPException(
            status_code=400,
            detail="You already have a pending organizer request"
        )

    # Create organizer request
    cursor.execute("""
        INSERT INTO organizer_requests
        (
            user_id,
            reason,
            organization
        )
        VALUES
        (
            %s,
            %s,
            %s
        )
        RETURNING request_id;
    """, (
        user_id,
        reason,
        organization
    ))

    request_id = cursor.fetchone()[0]

    connection.commit()

    cursor.close()
    connection.close()

    return {
        "message": "Organizer request submitted successfully",
        "request_id": request_id,
        "user_id": user_id,
        "status": "PENDING"
    }


@app.get("/events/{event_id}/registrations")
def get_event_registrations(
    event_id: int,
    organizer_id = Depends(get_current_organizer)
):

    connection = get_connection()
    cursor = connection.cursor()

    # Check whether the event exists
    cursor.execute("""
        SELECT event_id, title, organizer_id
        FROM events
        WHERE event_id = %s;
    """, (event_id,))

    event = cursor.fetchone()

    if event is None:
        cursor.close()
        connection.close()

        raise HTTPException(
            status_code=404,
            detail="Event not found"
        )

    # Check whether the logged-in organizer owns this event
    if event[2] != organizer_id:
        cursor.close()
        connection.close()

        raise HTTPException(
            status_code=403,
            detail="You do not own this event"
        )

    # Get students registered for this event
    cursor.execute("""
        SELECT
            r.registration_id,
            s.student_id,
            s.name,
            s.roll_no,
            s.branch,
            s.year,
            r.registered_at,
            r.status
        FROM registrations r
        JOIN students s
            ON r.student_id = s.student_id
        WHERE r.event_id = %s
        AND r.status = 'REGISTERED'
        ORDER BY r.registered_at;
       
    """, (event_id,))

    registrations = cursor.fetchall()

    cursor.close()
    connection.close()

    result = []

    for registration in registrations:
        result.append({
            "registration_id": registration[0],
            "student_id": registration[1],
            "name": registration[2],
            "roll_no": registration[3],
            "branch": registration[4],
            "year": registration[5],
            "registered_at": str(registration[6]),
            "status": registration[7]
        })

    return {
        "event_id": event[0],
        "event_title": event[1],
        "total_registrations": len(result),
        "registrations": result
    }

@app.post("/events")
def create_event(
    title: str,
    description: str,
    venue: str,
    event_date: str,
    event_time: str,
    duration_minutes: int,
    category: str,
    organizer_id = Depends(get_current_organizer)
):

    connection = get_connection()
    cursor = connection.cursor()

    # Combine event date and event time
    event_start = datetime.strptime(
        f"{event_date.strip()} {event_time.strip()}",
        "%Y-%m-%d %H:%M:%S"
    )

    # Registration closes 15 minutes before event starts
    registration_deadline = event_start - timedelta(minutes=15)

    # Insert event
    cursor.execute("""
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
            registration_deadline
        )
        VALUES
        (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s
        )
        RETURNING event_id;
    """, (
        organizer_id,
        title,
        description,
        venue,
        event_date,
        event_time,
        duration_minutes,
        category,
        registration_deadline
    ))

    event_id = cursor.fetchone()[0]

    connection.commit()

    cursor.close()
    connection.close()

    return {
        "message": "Event created successfully",
        "event_id": event_id,
        "organizer_id": organizer_id,
        "title": title,
        "registration_deadline": str(registration_deadline)
    }

@app.get("/organizers/me/events")
def get_my_events(
    organizer_id = Depends(get_current_organizer)
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            e.event_id,
            e.title,
            e.description,
            e.venue,
            e.event_date,
            e.event_time,
            e.duration_minutes,
            e.category,
            e.registration_deadline,
            e.status,
            COUNT(r.registration_id) AS registered_students
        FROM events e
        LEFT JOIN registrations r
            ON e.event_id = r.event_id
            AND r.status = 'REGISTERED'
        WHERE e.organizer_id = %s
        GROUP BY
            e.event_id,
            e.title,
            e.description,
            e.venue,
            e.event_date,
            e.event_time,
            e.duration_minutes,
            e.category,
            e.registration_deadline,
            e.status
        ORDER BY e.event_date, e.event_time;
    """, (organizer_id,))

    events = cursor.fetchall()

    cursor.close()
    connection.close()

    result = []

    for event in events:
        result.append({
            "event_id": event[0],
            "title": event[1],
            "description": event[2],
            "venue": event[3],
            "event_date": str(event[4]),
            "event_time": str(event[5]),
            "duration_minutes": event[6],
            "category": event[7],
            "registration_deadline": str(event[8]),
            "status": event[9],
            "registered_students": event[10]
        })

    return {
        "total_events": len(result),
        "events": result
    }

@app.put("/events/{event_id}")
def update_event(
    event_id: int,
    title: str,
    description: str,
    venue: str,
    event_date: str,
    event_time: str,
    duration_minutes: int,
    category: str
):

    connection = get_connection()
    cursor = connection.cursor()

    # Check whether event exists
    cursor.execute("""
        SELECT event_id
        FROM events
        WHERE event_id = %s;
    """, (event_id,))

    event = cursor.fetchone()

    if event is None:
        cursor.close()
        connection.close()

        return {
            "error": "Event not found"
        }

    # Combine updated event date and time
    event_start = datetime.strptime(
        f"{event_date.strip()} {event_time.strip()}",
        "%Y-%m-%d %H:%M:%S"
    )

    # Registration closes 15 minutes before event starts
    registration_deadline = event_start - timedelta(minutes=15)

    # Update event
    cursor.execute("""
        UPDATE events
        SET
            title = %s,
            description = %s,
            venue = %s,
            event_date = %s,
            event_time = %s,
            duration_minutes = %s,
            category = %s,
            registration_deadline = %s
        WHERE event_id = %s;
    """, (
        title,
        description,
        venue,
        event_date,
        event_time,
        duration_minutes,
        category,
        registration_deadline,
        event_id
    ))

    connection.commit()

    cursor.close()
    connection.close()

    return {
        "message": "Event updated successfully",
        "event_id": event_id,
        "title": title,
        "registration_deadline": str(registration_deadline)
    }

@app.delete("/events/{event_id}")
def delete_event(
    event_id: int,
    organizer_id = Depends(get_current_organizer)
):
    connection = get_connection()
    cursor = connection.cursor()

    # Check whether the event exists
    cursor.execute("""
        SELECT event_id, organizer_id, status
        FROM events
        WHERE event_id = %s;
    """, (event_id,))

    event = cursor.fetchone()

    if event is None:
        cursor.close()
        connection.close()

        raise HTTPException(
            status_code=404,
            detail="Event not found"
        )

    # Check whether the logged-in organizer owns the event
    if event[1] != organizer_id:
        cursor.close()
        connection.close()

        raise HTTPException(
            status_code=403,
            detail="You do not own this event"
        )

    # Check whether event is already cancelled
    if event[2] == "CANCELLED":
        cursor.close()
        connection.close()

        return {
            "error": "Event is already cancelled",
            "event_id": event_id
        }

    # Soft cancel the event
    cursor.execute("""
        UPDATE events
        SET status = 'CANCELLED'
        WHERE event_id = %s;
    """, (event_id,))

    connection.commit()

    cursor.close()
    connection.close()

    return {
        "message": "Event cancelled successfully",
        "event_id": event_id,
        "organizer_id": organizer_id,
        "status": "CANCELLED"
    }

@app.post("/signup")
def signup(
    email: str,
    password: str,
    name: str,
    roll_no: str,
    branch: str,
    year: int
):

    connection = get_connection()
    cursor = connection.cursor()

    # Check whether email already exists
    cursor.execute("""
        SELECT user_id
        FROM users
        WHERE email = %s;
    """, (email,))

    existing_user = cursor.fetchone()

    if existing_user is not None:
        cursor.close()
        connection.close()

        return {
            "error": "Email already registered"
        }

    # Hash the password before storing it
    hashed_password = password_hash.hash(password)

    try:

        # Create user account
        cursor.execute("""
            INSERT INTO users
            (
                email,
                password_hash
            )
            VALUES
            (
                %s,
                %s
            )
            RETURNING user_id;
        """, (
            email,
            hashed_password
        ))

        user_id = cursor.fetchone()[0]

        # Create student profile
        cursor.execute("""
            INSERT INTO students
            (
                user_id,
                name,
                roll_no,
                branch,
                year
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s
            )
            RETURNING student_id;
        """, (
            user_id,
            name,
            roll_no,
            branch,
            year
        ))

        student_id = cursor.fetchone()[0]

        # Save both operations permanently
        connection.commit()

    except Exception as error:

        # Undo everything if something went wrong
        connection.rollback()

        cursor.close()
        connection.close()

        return {
            "error": "Signup failed",
            "details": str(error)
        }

    cursor.close()
    connection.close()

    return {
        "message": "Student account created successfully",
        "user_id": user_id,
        "student_id": student_id,
        "email": email
    }

@app.post("/login")
def login(
    email: str,
    password: str
):

    connection = get_connection()
    cursor = connection.cursor()

    # Find the user by email
    cursor.execute("""
        SELECT
            user_id,
            password_hash,
            status
        FROM users
        WHERE email = %s;
    """, (email,))

    user = cursor.fetchone()

    # User does not exist
    if user is None:
        cursor.close()
        connection.close()

        return {
            "error": "Invalid email or password"
        }

    user_id = user[0]

    stored_password_hash = user[1]
    user_status = user[2]

    # Check whether account is active
    if user_status != "ACTIVE":
        cursor.close()
        connection.close()

        return {
            "error": "Account is inactive"
        }

    # Verify entered password against stored hash
    password_is_correct = password_hash.verify(
        password,
        stored_password_hash
    )

    if not password_is_correct:
        cursor.close()
        connection.close()

        return {
            "error": "Invalid email or password"
        }

    # Find student profile
    cursor.execute("""
        SELECT student_id
        FROM students
        WHERE user_id = %s;
    """, (user_id,))

    student = cursor.fetchone()

    # Find organizer profile
    cursor.execute("""
        SELECT organizer_id
        FROM organizers
        WHERE user_id = %s;
    """, (user_id,))

    organizer = cursor.fetchone()

    # Find admin profile
    cursor.execute("""
        SELECT admin_id
        FROM admins
        WHERE user_id = %s;
    """, (user_id,))

    admin = cursor.fetchone()

    cursor.close()
    connection.close()

    roles = []

    if student is not None:
        roles.append("student")

    if organizer is not None:
        roles.append("organizer")

    if admin is not None:
        roles.append("admin")



    token_data = {
        "user_id": user_id,
        "email": email,
        "roles": roles,
        "exp": datetime.utcnow() + timedelta(hours=2)
    }

    token = jwt.encode(
        token_data,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return {
        "message": "Login successful",
        "access_token": token,
        "token_type": "bearer",
        "user_id": user_id,
        "email": email,
        "roles": roles
    }

@app.post("/forgot-password")
def forgot_password(email: str):

    connection = get_connection()
    cursor = connection.cursor()

    # Check whether user exists
    cursor.execute("""
        SELECT user_id
        FROM users
        WHERE email = %s;
    """, (email,))

    user = cursor.fetchone()

    if user is None:
        cursor.close()
        connection.close()

        return {
            "message": "If this email is registered, a password reset link can be generated."
        }

    user_id = user[0]

    # Generate a secure random reset token
    reset_token = secrets.token_urlsafe(32)

    # Store only the hash of the token in the database
    token_hash = hashlib.sha256(
        reset_token.encode()
    ).hexdigest()

    # Token will expire after 30 minutes
    expires_at = datetime.now() + timedelta(minutes=30)

    # Save reset token in database
    cursor.execute("""
        INSERT INTO password_reset_tokens
        (
            user_id,
            token_hash,
            expires_at
        )
        VALUES
        (
            %s,
            %s,
            %s
        );
    """, (
        user_id,
        token_hash,
        expires_at
    ))

    connection.commit()

    cursor.close()
    connection.close()

    return {
    "message": "User found. Password reset process can continue.",
    "user_id": user_id,
    "reset_token": reset_token
    }  


@app.post("/reset-password")
def reset_password(
    token: str,
    new_password: str
):
    connection = get_connection()
    cursor = connection.cursor()

    token_hash = hashlib.sha256(
        token.encode()
    ).hexdigest()

    cursor.execute("""
        SELECT id, user_id
        FROM password_reset_tokens
        WHERE token_hash = %s
          AND used = FALSE
          AND expires_at > CURRENT_TIMESTAMP;
    """, (token_hash,))

    reset_record = cursor.fetchone()

    if reset_record is None:
        cursor.close()
        connection.close()

        raise HTTPException(
            status_code=400,
            detail="Invalid or expired reset token."
        )

    reset_id = reset_record[0]
    user_id = reset_record[1]

    new_password_hash = password_hash.hash(new_password)

    cursor.execute("""
        UPDATE users
        SET password_hash = %s
        WHERE user_id = %s;
    """, (
        new_password_hash,
        user_id
    ))

    cursor.execute("""
        UPDATE password_reset_tokens
        SET used = TRUE
        WHERE id = %s;
    """, (reset_id,))

    connection.commit()

    cursor.close()
    connection.close()

    return {
        "message": "Password reset successful."
        
    }
