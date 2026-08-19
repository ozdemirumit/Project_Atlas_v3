from app.models.identity import LocalCredential, Role, User, UserRole
from app.core.security import hash_password
from app.rbac.permissions import ADMINISTRATOR_ROLE


def _login_as_administrator(client, db_session, subject_id: str) -> None:
    user = User(subject_id=subject_id, display_name=subject_id, identity_source="local")
    db_session.add(user)
    db_session.flush()
    db_session.add(LocalCredential(user_id=user.id, password_hash=hash_password("correct-horse")))
    role = db_session.query(Role).filter(Role.name == ADMINISTRATOR_ROLE).one()
    db_session.add(UserRole(user_id=user.id, role_id=role.id))
    db_session.commit()
    login = client.post("/api/auth/login/local", json={"username": subject_id, "password": "correct-horse"})
    assert login.status_code == 204


def test_search_requires_permission(client):
    client.post("/api/auth/login/development")
    response = client.get("/api/knowledge/search", params={"q": "storage"})
    assert response.status_code == 403


def test_ingest_and_search(client, db_session):
    _login_as_administrator(client, db_session, "knowledge-admin")

    create = client.post(
        "/api/knowledge/sources",
        json={
            "key": "san-runbook",
            "title": "SAN Fabric Runbook",
            "content": (
                "Zoning conflicts on a SAN fabric occur when two initiators share an "
                "overlapping zone with conflicting storage targets.\n\n"
                "Backup jobs schedule nightly and use a dedicated backup zone."
            ),
        },
    )
    assert create.status_code == 201

    results = client.get("/api/knowledge/search", params={"q": "zoning conflict storage"})
    assert results.status_code == 200
    body = results.json()
    assert len(body) >= 1
    assert any("zoning" in item["content"].lower() for item in body)
    assert body[0]["score"] > 0


def test_duplicate_source_key_conflicts(client, db_session):
    _login_as_administrator(client, db_session, "knowledge-admin-2")
    payload = {"key": "dup-source", "title": "Dup", "content": "some content here"}
    first = client.post("/api/knowledge/sources", json=payload)
    assert first.status_code == 201
    second = client.post("/api/knowledge/sources", json=payload)
    assert second.status_code == 409
