"""Flask extension instances configured for the application.

This module centralizes extension setup to avoid circular import issues.
All extensions (database, migrations, password hashing) are initialized
here and then bound to the Flask app in the create_app() factory.
"""

from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

# Database ORM instance
db = SQLAlchemy()

# Database migration management
migrate = Migrate()

# Password hashing utility using bcrypt
bcrypt = Bcrypt()
