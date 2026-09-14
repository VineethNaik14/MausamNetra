"""
Securely create an ADMIN user.

This is the ONLY supported way to create an admin account. There is no
public API endpoint for admin registration, and no way for a normal user
to promote themselves - by design.

Usage (interactive, recommended):
    python scripts/create_admin.py

Usage (non-interactive, e.g. CI/CD or Docker entrypoint), reading from
environment variables ADMIN_NAME / ADMIN_EMAIL / ADMIN_PASSWORD:
    python scripts/create_admin.py --non-interactive
"""
import argparse
import getpass
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.security import hash_password  # noqa: E402
from app.db.database import SessionLocal  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402
from app.repositories.user_repository import UserRepository  # noqa: E402


def _validate_password(password: str) -> None:
    if len(password) < 10:
        raise ValueError("Password must be at least 10 characters long")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a mausamnetra ADMIN user")
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Read ADMIN_NAME / ADMIN_EMAIL / ADMIN_PASSWORD from environment instead of prompting",
    )
    args = parser.parse_args()

    if args.non_interactive:
        name = os.environ.get("ADMIN_NAME", "").strip()
        email = os.environ.get("ADMIN_EMAIL", "").strip().lower()
        password = os.environ.get("ADMIN_PASSWORD", "")
        if not (name and email and password):
            print("ERROR: ADMIN_NAME, ADMIN_EMAIL and ADMIN_PASSWORD must all be set for --non-interactive mode.")
            sys.exit(1)
    else:
        name = input("Admin full name: ").strip()
        email = input("Admin email: ").strip().lower()
        password = getpass.getpass("Admin password: ")
        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            print("ERROR: Passwords do not match.")
            sys.exit(1)

    try:
        _validate_password(password)
    except ValueError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    db = SessionLocal()
    try:
        repo = UserRepository(db)
        existing = repo.get_by_email(email)
        if existing:
            print(f"ERROR: A user with email '{email}' already exists (role={existing.role}).")
            sys.exit(1)

        admin = User(
            name=name,
            email=email,
            password_hash=hash_password(password),
            role=UserRole.ADMIN,
            is_active=True,
        )
        repo.create(admin)
        print(f"Admin user created successfully: {email} (id={admin.id})")
    finally:
        db.close()


if __name__ == "__main__":
    main()
