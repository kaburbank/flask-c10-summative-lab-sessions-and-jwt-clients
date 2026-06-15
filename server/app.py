"""Flask application factory and route handlers.

This module defines:
- create_app(): Factory function to create and configure the Flask app.
- Auth endpoints: signup, login, check_session, logout.
- Protected CRUD endpoints for the Note resource with pagination.
"""

from math import ceil

from flask import Flask, jsonify, request, session

from config import Config
from extensions import bcrypt, db, migrate
from models import Note, User


def create_app(test_config=None):
    """Create and configure the Flask application.
    
    Args:
        test_config: Optional dict of test-specific config overrides.
        
    Returns:
        Flask app instance with all routes registered.
    """
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)

    @app.get("/")
    def index():
        return jsonify({"message": "Session auth API is running"})

    @app.post("/signup")
    def signup():
        """Register a new user and start a session.
        
        Request JSON:
            username (str): New username (required).
            password (str): Password (required, min 8 chars).
            password_confirmation (str): Password confirmation (must match).
            
        Returns:
            201: {id, username} on success.
            400: {errors: [list of validation errors]} on invalid input.
        """
        data = request.get_json() or {}
        username = (data.get("username") or "").strip()
        password = data.get("password")
        password_confirmation = data.get("password_confirmation")

        errors = []
        if not username:
            errors.append("Username is required.")
        if not password:
            errors.append("Password is required.")
        if password != password_confirmation:
            errors.append("Password confirmation must match password.")
        if User.query.filter_by(username=username).first():
            errors.append("Username is already taken.")

        if errors:
            return jsonify({"errors": errors}), 400

        user = User(username=username)
        try:
            user.password_hash = password
        except ValueError as exc:
            return jsonify({"errors": [str(exc)]}), 400

        db.session.add(user)
        db.session.commit()

        session["user_id"] = user.id
        return jsonify(user.to_dict()), 201

    @app.post("/login")
    def login():
        """Authenticate a user and start a session.
        
        Request JSON:
            username (str): Username (required).
            password (str): Password (required).
            
        Returns:
            200: {id, username} on successful authentication.
            401: {errors: ["Invalid username or password."]} on failure.
        """
        data = request.get_json() or {}
        username = (data.get("username") or "").strip()
        password = data.get("password") or ""

        user = User.query.filter_by(username=username).first()
        if not user or not user.authenticate(password):
            return jsonify({"errors": ["Invalid username or password."]}), 401

        session["user_id"] = user.id
        return jsonify(user.to_dict()), 200

    @app.get("/check_session")
    def check_session():
        """Check if user is currently logged in via session.
        
        Returns:
            200: {id, username} if logged in, {} if not logged in.
        """
        user = current_user()
        if not user:
            return jsonify({}), 200
        return jsonify(user.to_dict()), 200

    @app.delete("/logout")
    def logout():
        """End the user session and log out.
        
        Returns:
            200: {} (empty response on success).
        """
        session.pop("user_id", None)
        return jsonify({}), 200

    @app.get("/notes")
    def notes_index():
        """Retrieve paginated notes for the logged-in user.
        
        Query Parameters:
            page (int): Page number (default 1, min 1).
            per_page (int): Notes per page (default 10, min 1, max 50).
            
        Returns:
            200: {data: [notes], meta: {page, per_page, total, total_pages}}.
            401: {errors: ["Unauthorized"]} if not logged in.
        """
        user = require_auth()
        if user is None:
            return jsonify({"errors": ["Unauthorized"]}), 401

        page = max(int(request.args.get("page", 1)), 1)
        per_page = min(max(int(request.args.get("per_page", 10)), 1), 50)

        pagination = (
            Note.query.filter_by(user_id=user.id)
            .order_by(Note.created_at.desc())
            .paginate(page=page, per_page=per_page, error_out=False)
        )

        return (
            jsonify(
                {
                    "data": [note.to_dict() for note in pagination.items],
                    "meta": {
                        "page": page,
                        "per_page": per_page,
                        "total": pagination.total,
                        "total_pages": ceil(pagination.total / per_page)
                        if pagination.total
                        else 0,
                    },
                }
            ),
            200,
        )

    @app.post("/notes")
    def notes_create():
        """Create a new note for the logged-in user.
        
        Request JSON:
            title (str): Note title (required, non-empty).
            content (str): Note body (required, non-empty).
            
        Returns:
            201: Full note object on success.
            400: {errors: [list of validation errors]} on invalid input.
            401: {errors: ["Unauthorized"]} if not logged in.
        """
        user = require_auth()
        if user is None:
            return jsonify({"errors": ["Unauthorized"]}), 401

        data = request.get_json() or {}
        title = (data.get("title") or "").strip()
        content = (data.get("content") or "").strip()

        errors = []
        if not title:
            errors.append("Title is required.")
        if not content:
            errors.append("Content is required.")

        if errors:
            return jsonify({"errors": errors}), 400

        note = Note(title=title, content=content, user_id=user.id)
        db.session.add(note)
        db.session.commit()
        return jsonify(note.to_dict()), 201

    @app.patch("/notes/<int:note_id>")
    def notes_update(note_id):
        """Update an existing note owned by the logged-in user.
        
        Args:
            note_id: ID of the note to update.
            
        Request JSON (partial update):
            title (str, optional): New note title (non-empty if provided).
            content (str, optional): New note body (non-empty if provided).
            
        Returns:
            200: Updated note object on success.
            400: {errors: ["Title/Content cannot be blank."]} on invalid input.
            401: {errors: ["Unauthorized"]} if not logged in.
            404: {errors: ["Note not found"]} if note doesn't exist or belongs to another user.
        """
        user = require_auth()
        if user is None:
            return jsonify({"errors": ["Unauthorized"]}), 401

        note = Note.query.filter_by(id=note_id, user_id=user.id).first()
        if not note:
            return jsonify({"errors": ["Note not found"]}), 404

        data = request.get_json() or {}
        if "title" in data:
            title = (data.get("title") or "").strip()
            if not title:
                return jsonify({"errors": ["Title cannot be blank."]}), 400
            note.title = title

        if "content" in data:
            content = (data.get("content") or "").strip()
            if not content:
                return jsonify({"errors": ["Content cannot be blank."]}), 400
            note.content = content

        db.session.commit()
        return jsonify(note.to_dict()), 200

    @app.delete("/notes/<int:note_id>")
    def notes_delete(note_id):
        """Delete a note owned by the logged-in user.
        
        Args:
            note_id: ID of the note to delete.
            
        Returns:
            200: {} (empty response) on success.
            401: {errors: ["Unauthorized"]} if not logged in.
            404: {errors: ["Note not found"]} if note doesn't exist or belongs to another user.
        """
        user = require_auth()
        if user is None:
            return jsonify({"errors": ["Unauthorized"]}), 401

        note = Note.query.filter_by(id=note_id, user_id=user.id).first()
        if not note:
            return jsonify({"errors": ["Note not found"]}), 404

        db.session.delete(note)
        db.session.commit()
        return jsonify({}), 200

    def current_user():
        """Retrieve the User object for the current session, if any.
        
        Returns:
            User: User model instance if logged in, None otherwise.
        """
        user_id = session.get("user_id")
        if not user_id:
            return None
        return db.session.get(User, user_id)

    def require_auth():
        """Check if user is authenticated (convenience wrapper).
        
        Returns:
            User: Logged-in User or None.
        """
        return current_user()

    return app


app = create_app()


if __name__ == "__main__":
    app.run(port=5555, debug=True)
