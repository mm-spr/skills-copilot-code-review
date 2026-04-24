# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Sign up for activities
- View active announcements on the homepage
- Manage announcements from the staff header dialog after signing in

## Getting Started

1. Install the dependencies:

   ```bash
   python -m pip install --requirement ../requirements.txt
   ```

2. Run the application:

   ```bash
   python app.py
   ```

3. Open your browser and go to:
   - API documentation: <http://localhost:8000/docs>
   - Alternative documentation: <http://localhost:8000/redoc>

## API Endpoints

- `GET /activities`: Get all activities with their details and current participant count.
- `POST /activities/{activity_name}/signup?email=student@mergington.edu`: Sign up for an activity.
- `POST /activities/{activity_name}/unregister?email=student@mergington.edu`: Remove a student from an activity.
- `POST /auth/login?username=principal&password=admin789`: Sign in a teacher or administrator.
- `GET /auth/check-session?username=principal`: Validate a signed-in user.
- `GET /announcements`: Get currently active announcements.
- `GET /announcements/manage?teacher_username=principal`: Get all announcements for the management dialog.
- `POST /announcements?teacher_username=principal`: Create a new announcement.
- `PUT /announcements/{announcement_id}?teacher_username=principal`: Update an announcement.
- `DELETE /announcements/{announcement_id}?teacher_username=principal`: Delete an announcement.

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Teachers** - Uses username as identifier:
   - Display name
   - Role
   - Argon2-hashed password

3. **Announcements** - Uses generated identifiers:
   - Title
   - Message
   - Optional start date
   - Required expiration date
   - Created and updated timestamps

All data is stored in MongoDB. The application seeds sample activities, teacher accounts, and an example announcement during database initialization when the collections are empty.
