def test_signup_login_check_session_logout_flow(client):
    signup = client.post(
        "/signup",
        json={
            "username": "alice",
            "password": "password123",
            "password_confirmation": "password123",
        },
    )
    assert signup.status_code == 201
    assert signup.get_json()["username"] == "alice"

    check = client.get("/check_session")
    assert check.status_code == 200
    assert check.get_json()["username"] == "alice"

    logout = client.delete("/logout")
    assert logout.status_code == 200
    assert logout.get_json() == {}

    login = client.post("/login", json={"username": "alice", "password": "password123"})
    assert login.status_code == 200
    assert login.get_json()["username"] == "alice"


def test_auth_validation_and_errors(client):
    bad_signup = client.post(
        "/signup",
        json={
            "username": "",
            "password": "short",
            "password_confirmation": "mismatch",
        },
    )
    assert bad_signup.status_code == 400
    assert "errors" in bad_signup.get_json()

    short_password = client.post(
        "/signup",
        json={
            "username": "tiny_pw",
            "password": "short",
            "password_confirmation": "short",
        },
    )
    assert short_password.status_code == 400
    assert "Password must be at least 8 characters long." in short_password.get_json()["errors"]

    wrong_login = client.post("/login", json={"username": "nobody", "password": "bad"})
    assert wrong_login.status_code == 401
    assert "errors" in wrong_login.get_json()


def test_unauthorized_users_cannot_access_notes(client):
    res = client.get("/notes")
    assert res.status_code == 401
    assert res.get_json()["errors"] == ["Unauthorized"]


def test_notes_crud_and_pagination_for_owner(client):
    client.post(
        "/signup",
        json={
            "username": "owner",
            "password": "password123",
            "password_confirmation": "password123",
        },
    )

    created_ids = []
    for i in range(3):
        created = client.post("/notes", json={"title": f"n{i}", "content": "body"})
        assert created.status_code == 201
        created_ids.append(created.get_json()["id"])

    paged = client.get("/notes?page=1&per_page=2")
    assert paged.status_code == 200
    body = paged.get_json()
    assert len(body["data"]) == 2
    assert body["meta"]["page"] == 1
    assert body["meta"]["per_page"] == 2
    assert body["meta"]["total"] == 3
    assert body["meta"]["total_pages"] == 2

    updated = client.patch(f"/notes/{created_ids[0]}", json={"title": "updated"})
    assert updated.status_code == 200
    assert updated.get_json()["title"] == "updated"

    deleted = client.delete(f"/notes/{created_ids[0]}")
    assert deleted.status_code == 200


def test_user_cannot_modify_another_users_note(app):
    alice = app.test_client()
    bob = app.test_client()

    alice.post(
        "/signup",
        json={
            "username": "alice2",
            "password": "password123",
            "password_confirmation": "password123",
        },
    )
    note = alice.post("/notes", json={"title": "private", "content": "secret"})
    note_id = note.get_json()["id"]

    bob.post(
        "/signup",
        json={
            "username": "bob2",
            "password": "password123",
            "password_confirmation": "password123",
        },
    )

    cross_patch = bob.patch(f"/notes/{note_id}", json={"title": "hacked"})
    assert cross_patch.status_code == 404
    assert cross_patch.get_json()["errors"] == ["Note not found"]

    cross_delete = bob.delete(f"/notes/{note_id}")
    assert cross_delete.status_code == 404
    assert cross_delete.get_json()["errors"] == ["Note not found"]
