from app.core.security import hash_password
from app.models.identity import LocalCredential, User


def test_me_requires_authentication(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_development_login_grants_only_self_read(client):
    response = client.post("/api/auth/login/development")
    assert response.status_code == 204
    assert client.cookies.get("atlas_session") is not None

    me = client.get("/api/auth/me")
    assert me.status_code == 200
    body = me.json()
    assert body["subject_id"] == "local-operator"
    assert body["permissions"] == ["identity.self.read"]


def test_development_login_cannot_read_audit(client):
    client.post("/api/auth/login/development")
    response = client.get("/api/audit/events")
    assert response.status_code == 403


def test_local_login_with_wrong_password_is_rejected(client, db_session):
    user = User(subject_id="alice", display_name="Alice", identity_source="local")
    db_session.add(user)
    db_session.flush()
    db_session.add(LocalCredential(user_id=user.id, password_hash=hash_password("correct-horse")))
    db_session.commit()

    response = client.post(
        "/api/auth/login/local", json={"username": "alice", "password": "wrong-password"}
    )
    assert response.status_code == 401
    assert client.cookies.get("atlas_session") is None


def test_local_login_with_correct_password_succeeds(client, db_session):
    user = User(subject_id="bob", display_name="Bob", identity_source="local")
    db_session.add(user)
    db_session.flush()
    db_session.add(LocalCredential(user_id=user.id, password_hash=hash_password("correct-horse")))
    db_session.commit()

    response = client.post(
        "/api/auth/login/local", json={"username": "bob", "password": "correct-horse"}
    )
    assert response.status_code == 204
    assert client.cookies.get("atlas_session") is not None


def test_logout_invalidates_session(client):
    client.post("/api/auth/login/development")
    assert client.get("/api/auth/me").status_code == 200

    logout = client.post("/api/auth/logout")
    assert logout.status_code == 204

    assert client.get("/api/auth/me").status_code == 401


def test_unknown_username_and_wrong_password_return_identical_error(client):
    unknown = client.post(
        "/api/auth/login/local", json={"username": "does-not-exist", "password": "whatever"}
    )
    assert unknown.status_code == 401
    assert unknown.json()["detail"] == "Invalid credentials."
