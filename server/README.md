# Session-Based Notes API

A secure Flask backend API that manages user authentication, note creation, and retrieval with session-based authorization. Users can create, read, update, and delete their own notes with full privacy isolation.

## Project Description

This is a production-ready Flask API implementing:
- **Session-based authentication** using Flask sessions and secure cookies
- **Password security** via bcrypt hashing
- **Database migrations** with Flask-Migrate (Alembic)
- **User-scoped resources** (notes) with full CRUD operations
- **Pagination** on list endpoints for scalability
- **Authorization checks** to prevent cross-user data access
- **Comprehensive error handling** with descriptive validation messages
- **Automated test suite** for endpoint verification

### Tech Stack
- **Framework**: Flask 3.0.3
- **ORM**: SQLAlchemy (via Flask-SQLAlchemy 3.1.1)
- **Migrations**: Flask-Migrate 4.0.7
- **Password Hashing**: Flask-Bcrypt 1.0.1
- **Testing**: pytest 8.2.2
- **Database**: SQLite (default, configurable)

---

## Installation

### Prerequisites
- Python 3.10+
- `pip` or `pipenv`

### Steps

1. **Navigate to the server directory**
   ```bash
   cd server
   ```

2. **Create a virtual environment** (optional but recommended)
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run database migrations**
   ```bash
   export FLASK_APP=app.py  # On Windows: set FLASK_APP=app.py
   flask db upgrade
   ```

5. **(Optional) Seed sample data**
   ```bash
   python seed.py
   ```

---

## Running the Application

### Start the development server
```bash
python app.py
```

The API will run on `http://localhost:5555`

### Run automated tests
```bash
pytest
```

All 5 tests should pass with no warnings.

---

## Project Structure

```
server/
├── app.py                 # Flask app factory and route handlers
├── models.py              # SQLAlchemy User and Note models
├── extensions.py          # Centralized Flask extension setup
├── config.py              # Configuration management
├── seed.py                # Database seeding script
├── requirements.txt       # Python dependencies
├── pytest.ini             # Pytest configuration
├── .gitignore             # Git ignore rules
├── migrations/            # Alembic migration scripts
│   └── versions/          # Versioned migration files
└── tests/                 # Automated test suite
    ├── conftest.py        # pytest fixtures and configuration
    └── test_auth_and_notes.py  # endpoint tests
```

---

## API Endpoints

### Authentication Routes

#### POST `/signup`
Register a new user and start a session.

**Request:**
```json
{
  "username": "alice",
  "password": "password123",
  "password_confirmation": "password123"
}
```

**Success Response:** `201 Created`
```json
{
  "id": 1,
  "username": "alice"
}
```

**Error Response:** `400 Bad Request`
```json
{
  "errors": [
    "Username is required.",
    "Password confirmation must match password.",
    "Password must be at least 8 characters long."
  ]
}
```

---

#### POST `/login`
Authenticate an existing user via username/password and start a session.

**Request:**
```json
{
  "username": "alice",
  "password": "password123"
}
```

**Success Response:** `200 OK`
```json
{
  "id": 1,
  "username": "alice"
}
```

**Error Response:** `401 Unauthorized`
```json
{
  "errors": ["Invalid username or password."]
}
```

---

#### GET `/check_session`
Verify the current user's session status. Returns user if logged in, empty object if not.

**Response:** `200 OK`

*If logged in:*
```json
{
  "id": 1,
  "username": "alice"
}
```

*If not logged in:*
```json
{}
```

---

#### DELETE `/logout`
End the user's session and clear authentication.

**Response:** `200 OK`
```json
{}
```

---

### Note Resource Routes

#### GET `/notes`
Retrieve a paginated list of notes for the logged-in user (most recent first).

**Query Parameters:**
- `page` (optional, default=1): Page number (1-indexed)
- `per_page` (optional, default=10): Notes per page (1-50)

**Success Response:** `200 OK`
```json
{
  "data": [
    {
      "id": 1,
      "title": "Grocery List",
      "content": "Milk, eggs, bread",
      "user_id": 1,
      "created_at": "2026-06-15T14:53:31+00:00",
      "updated_at": "2026-06-15T14:53:31+00:00"
    }
  ],
  "meta": {
    "page": 1,
    "per_page": 10,
    "total": 5,
    "total_pages": 1
  }
}
```

**Error Response:** `401 Unauthorized`
```json
{
  "errors": ["Unauthorized"]
}
```

---

#### POST `/notes`
Create a new note for the logged-in user.

**Request:**
```json
{
  "title": "Workout Plan",
  "content": "Monday: chest and triceps"
}
```

**Success Response:** `201 Created`
```json
{
  "id": 2,
  "title": "Workout Plan",
  "content": "Monday: chest and triceps",
  "user_id": 1,
  "created_at": "2026-06-15T14:54:00+00:00",
  "updated_at": "2026-06-15T14:54:00+00:00"
}
```

**Error Response:** `400 Bad Request`
```json
{
  "errors": ["Title is required.", "Content is required."]
}
```

**Error Response:** `401 Unauthorized`
```json
{
  "errors": ["Unauthorized"]
}
```

---

#### PATCH `/notes/<note_id>`
Update an existing note (title, content, or both). Only the logged-in note owner can update.

**Parameters:**
- `note_id` (path): ID of the note to update

**Request (partial update, either field optional):**
```json
{
  "title": "Updated Title",
  "content": "Updated content"
}
```

**Success Response:** `200 OK`
```json
{
  "id": 2,
  "title": "Updated Title",
  "content": "Updated content",
  "user_id": 1,
  "created_at": "2026-06-15T14:54:00+00:00",
  "updated_at": "2026-06-15T15:00:00+00:00"
}
```

**Error Response:** `400 Bad Request` (if updating field to empty)
```json
{
  "errors": ["Title cannot be blank."]
}
```

**Error Response:** `401 Unauthorized`
```json
{
  "errors": ["Unauthorized"]
}
```

**Error Response:** `404 Not Found` (note doesn't exist or belongs to another user)
```json
{
  "errors": ["Note not found"]
}
```

---

#### DELETE `/notes/<note_id>`
Delete a note owned by the logged-in user.

**Parameters:**
- `note_id` (path): ID of the note to delete

**Success Response:** `200 OK`
```json
{}
```

**Error Response:** `401 Unauthorized`
```json
{
  "errors": ["Unauthorized"]
}
```

**Error Response:** `404 Not Found`
```json
{
  "errors": ["Note not found"]
}
```

---

## Security Features

1. **Password Hashing**: All passwords are hashed with bcrypt (min 8 characters required)
2. **Session Management**: User sessions are stored server-side with secure cookies
3. **Authorization**: All note endpoints require valid session; users can only access their own notes
4. **Input Validation**: All inputs are validated and errors returned with descriptive messages
5. **Cross-User Isolation**: Database queries filter by current user's ID to prevent unauthorized access

---

## Testing

The automated test suite covers:
- User signup/login/logout flow
- Password validation and error handling
- Unauthorized access blocking
- Note CRUD operations
- Pagination functionality
- Cross-user data isolation

Run tests:
```bash
pytest
```

Expected output:
```
5 passed in 1.67s
```

---

## Configuration

Edit `config.py` to customize:
- `SECRET_KEY`: Flask session secret (change for production)
- `SQLALCHEMY_DATABASE_URI`: Database URL (default: SQLite in project root)
- `SQLALCHEMY_TRACK_MODIFICATIONS`: SQLAlchemy behavior flag

For production, set environment variables:
```bash
export FLASK_ENV=production
export SECRET_KEY="your-secure-random-key"
export DATABASE_URI="postgresql://user:password@localhost/dbname"
```

---

## Troubleshooting

**Migration error on fresh setup:**
```bash
export FLASK_APP=app.py
flask db init
flask db migrate -m "initial schema"
flask db upgrade
```

**Port already in use:**
Edit `app.py` and change `app.run(port=5555)` to a different port.

**Database locked (SQLite):**
Delete `app.db` and re-run migrations.

---

## License

This is a summative lab project for educational purposes.
