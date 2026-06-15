# Session-Based Flask API

This backend implements:
- User signup/login/logout using Flask sessions
- Secure password hashing
- A user-owned `notes` resource
- Protected CRUD endpoints for notes
- Pagination on the notes index route

## Endpoints

### Auth
- `POST /signup`
- `POST /login`
- `GET /check_session`
- `DELETE /logout`

### Notes
- `GET /notes?page=1&per_page=10`
- `POST /notes`
- `PATCH /notes/<note_id>`
- `DELETE /notes/<note_id>`

All notes routes require a valid logged-in session and only expose notes for the current user.

## Run

```bash
cd server
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

The API runs on `http://localhost:5555`.
