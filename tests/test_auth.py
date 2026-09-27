def test_first_registered_user_becomes_admin(register):
    resp = register("admin_user", "Secr3tPassword!")
    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == "admin_user"
    assert data["role"] == "admin"


def test_subsequent_users_have_user_role(register):
    register("first_admin", "Secr3tPassword!")
    resp2 = register("regular_joe", "Secr3tPassword!", "Joe Regular")
    assert resp2.status_code == 201
    data = resp2.json()
    assert data["username"] == "regular_joe"
    assert data["role"] == "user"


def test_duplicate_username_returns_bad_request(register):
    register("cloned_user", "Secr3tPassword!")
    dup = register("cloned_user", "DifferentPassword123!")
    assert dup.status_code == 400
    assert "already registered" in dup.json()["detail"]


def test_login_success(register, client):
    register("auth_tester", "MyValidPassword123")
    resp = client.post(
        "/auth/login",
        data={"username": "auth_tester", "password": "MyValidPassword123"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["username"] == "auth_tester"


def test_login_invalid_password_returns_401(register, client):
    register("bad_password_user", "CorrectPassword123")
    resp = client.post(
        "/auth/login",
        data={"username": "bad_password_user", "password": "WrongPassword!"},
    )
    assert resp.status_code == 401
    assert "Incorrect username or password" in resp.json()["detail"]


def test_get_me_endpoint(admin_token, auth_header, client):
    resp = client.get("/auth/me", headers=auth_header(admin_token))
    assert resp.status_code == 200
    assert resp.json()["username"] == "sysadmin"
    assert resp.json()["role"] == "admin"


def test_admin_can_list_users(admin_token, user_token, auth_header, client):
    # Admin lists users
    resp_admin = client.get("/auth/users", headers=auth_header(admin_token))
    assert resp_admin.status_code == 200
    assert len(resp_admin.json()) >= 1

    # Regular user is forbidden
    resp_user = client.get("/auth/users", headers=auth_header(user_token))
    assert resp_user.status_code == 403
