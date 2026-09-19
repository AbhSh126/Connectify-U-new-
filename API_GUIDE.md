# ConnectifyU — Frontend API Guide

Backend: `http://127.0.0.1:8000`  
Swagger: `http://127.0.0.1:8000/docs`

The HTML/CSS/JavaScript frontend communicates with FastAPI APIs only.
The frontend must NOT connect directly to PostgreSQL.

## Authentication
`POST /login`

Protected requests use:
`Authorization: Bearer <access_token>`

`POST /signup`

## Student
- `GET /events`
- `GET /events/{event_id}`
- `POST /registrations` body: `{"event_id": 1}`
- `GET /students/me/registrations`
- `DELETE /registrations/{registration_id}`

## Organizer
- `POST /events`
- `GET /organizers/me/events`
- `PUT /events/{event_id}`
- `DELETE /events/{event_id}`
- `GET /events/{event_id}/registrations`

## Organizer request / Admin
- `POST /organizer-requests`
- `GET /admin/organizer-requests/pending`
- `POST /admin/organizer-requests/{request_id}/approve`
- `POST /admin/organizer-requests/{request_id}/reject`

## Password reset
- `POST /forgot-password`
- `POST /reset-password`

The current forgot-password implementation exposes a reset token only for local testing. Before production, this must be replaced by an emailed reset link and the token must not be returned in the response.

## Current behavior
- A student cannot register for their own event.
- Duplicate registration is rejected.
- Cancellation changes the registration to `CANCELLED`.
- Re-registering after cancellation is intentionally deferred until after the frontend MVP.
