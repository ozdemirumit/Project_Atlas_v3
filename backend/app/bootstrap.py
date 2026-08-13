"""ATLAS-030 Section 11 / ATLAS-038: local bootstrap administrator creation.

Run once against a freshly migrated database:

    python -m app.bootstrap

Generates the first local administrator credential, prints it exactly once
(never logged, never written to a file), and requires it to be changed on
first interactive login (`must_change_password`). Refuses to run if a local
administrator already exists.
"""
import secrets
import sys
import uuid

from app.audit.service import record_event
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.identity import LocalCredential, Role, User, UserRole
from app.rbac.permissions import ADMINISTRATOR_ROLE

BOOTSTRAP_SUBJECT_ID = "bootstrap-administrator"


def main() -> int:
    db = SessionLocal()
    try:
        existing = (
            db.query(User)
            .filter(User.identity_source == "local", User.subject_id == BOOTSTRAP_SUBJECT_ID)
            .one_or_none()
        )
        if existing is not None:
            print("A local bootstrap administrator already exists. Refusing to create another.")
            return 1

        role = db.query(Role).filter(Role.name == ADMINISTRATOR_ROLE).one_or_none()
        if role is None:
            print("Administrator role is not seeded. Run `alembic upgrade head` first.")
            return 1

        generated_password = secrets.token_urlsafe(18)

        user = User(
            subject_id=BOOTSTRAP_SUBJECT_ID,
            display_name="Bootstrap Administrator",
            email=None,
            identity_source="local",
            must_change_password=True,
        )
        db.add(user)
        db.flush()

        db.add(LocalCredential(user_id=user.id, password_hash=hash_password(generated_password)))
        db.add(UserRole(user_id=user.id, role_id=role.id))

        record_event(
            db,
            event_type="bootstrap.administrator.created",
            outcome="success",
            correlation_id=str(uuid.uuid4()),
            subject_id=user.subject_id,
        )
        db.commit()

        print("Local bootstrap administrator created.")
        print(f"  username: {BOOTSTRAP_SUBJECT_ID}")
        print(f"  password: {generated_password}")
        print("This password is shown once and is not stored anywhere in plain text.")
        print("You must change it on first login.")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
