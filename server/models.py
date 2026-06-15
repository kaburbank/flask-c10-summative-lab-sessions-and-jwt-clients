"""SQLAlchemy models for User and Note resources.

User represents an authenticated account with a secure password.
Note represents a text entry owned by a specific User.
"""

from datetime import timezone

from sqlalchemy import func

from extensions import bcrypt, db


class User(db.Model):
    """User account model with bcrypt password hashing.
    
    Attributes:
        id: Primary key.
        username: Unique username for login (string, 80 chars max).
        _password_hash: Bcrypt hashed password (internal, use password_hash property).
        notes: Relationship to all Note objects owned by this user.
    """
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    _password_hash = db.Column("password_hash", db.String(255), nullable=False)

    notes = db.relationship(
        "Note", backref="user", lazy=True, cascade="all, delete-orphan"
    )

    @property
    def password_hash(self):
        """Write-only property to prevent reading raw hashes."""
        raise AttributeError("Password hashes are write-only.")

    @password_hash.setter
    def password_hash(self, password):
        """Hash and store a plaintext password using bcrypt.
        
        Args:
            password: Plaintext password string (must be 8+ characters).
            
        Raises:
            ValueError: If password is missing or shorter than 8 characters.
        """
        if not password or len(password) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        self._password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def authenticate(self, password):
        """Verify if a plaintext password matches the stored hash.
        
        Args:
            password: Plaintext password string to check.
            
        Returns:
            bool: True if password matches, False otherwise.
        """
        return bcrypt.check_password_hash(self._password_hash, password)

    def to_dict(self):
        """Serialize user to JSON-safe dictionary.
        
        Returns:
            dict: User data (id, username) suitable for API responses.
        """
        return {"id": self.id, "username": self.username}


class Note(db.Model):
    """Note resource owned by a User.
    
    Attributes:
        id: Primary key.
        title: Note title (string, 120 chars max).
        content: Note body text (unlimited).
        created_at: Timestamp when note was created (UTC).
        updated_at: Timestamp when note was last modified (UTC).
        user_id: Foreign key to the owning User.
    """
    __tablename__ = "notes"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = db.Column(
        db.DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    def to_dict(self):
        """Serialize note to JSON-safe dictionary with ISO 8601 timestamps.
        
        Returns:
            dict: Note data suitable for API responses.
        """
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "user_id": self.user_id,
            "created_at": _iso(self.created_at),
            "updated_at": _iso(self.updated_at),
        }


def _iso(value):
    """Convert datetime to ISO 8601 string with timezone info.
    
    Args:
        value: datetime object or None.
        
    Returns:
        str: ISO 8601 formatted timestamp (e.g. '2026-06-15T14:53:31+00:00'), or None.
    """
    if not value:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()
