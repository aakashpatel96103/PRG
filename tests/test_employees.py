SAMPLE_EMPLOYEE = {
    "full_name": "Sarah Connor",
    "email": "sarah.connor@cyberdyne.com",
    "department": "Engineering",
    "position": "Security Systems Lead",
    "salary": 125000.0,
    "phone": "+1 (555) 019-2834",
    "status": "active",
}


def test_admin_can_create_employee(admin_token, auth_header, client):
    resp = client.post(
        "/employees/",
        json=SAMPLE_EMPLOYEE,
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["full_name"] == SAMPLE_EMPLOYEE["full_name"]
    assert data["email"] == SAMPLE_EMPLOYEE["email"]
    assert data["id"] is not None


def test_duplicate_employee_email_rejected(admin_token, auth_header, client):
    client.post("/employees/", json=SAMPLE_EMPLOYEE, headers=auth_header(admin_token))
    dup_resp = client.post(
        "/employees/", json=SAMPLE_EMPLOYEE, headers=auth_header(admin_token)
    )
    assert dup_resp.status_code == 400
    assert "already exists" in dup_resp.json()["detail"]


def test_invalid_employee_payload_rejected(admin_token, auth_header, client):
    invalid_payload = {
        "full_name": "X",
        "email": "not-an-email",
        "department": "IT",
        "position": "Tech",
        "salary": -500,  # Negative salary invalid
    }
    resp = client.post(
        "/employees/",
        json=invalid_payload,
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 422


def test_list_and_search_employees(admin_token, auth_header, client):
    client.post(
        "/employees/",
        json=SAMPLE_EMPLOYEE,
        headers=auth_header(admin_token),
    )
    client.post(
        "/employees/",
        json={
            "full_name": "John Doe",
            "email": "john.doe@marketing.com",
            "department": "Marketing",
            "position": "SEO Manager",
            "salary": 85000.0,
            "status": "active",
        },
        headers=auth_header(admin_token),
    )

    # All employees
    res_all = client.get("/employees/", headers=auth_header(admin_token))
    assert res_all.status_code == 200
    assert len(res_all.json()) == 2

    # Filter by department
    res_dept = client.get(
        "/employees/?department=Marketing", headers=auth_header(admin_token)
    )
    assert len(res_dept.json()) == 1
    assert res_dept.json()[0]["full_name"] == "John Doe"

    # Search query
    res_search = client.get("/employees/?q=Sarah", headers=auth_header(admin_token))
    assert len(res_search.json()) == 1
    assert res_search.json()[0]["email"] == "sarah.connor@cyberdyne.com"


def test_get_single_employee_and_404(admin_token, auth_header, client):
    create_res = client.post(
        "/employees/",
        json=SAMPLE_EMPLOYEE,
        headers=auth_header(admin_token),
    )
    emp_id = create_res.json()["id"]

    # Valid ID
    get_res = client.get(f"/employees/{emp_id}", headers=auth_header(admin_token))
    assert get_res.status_code == 200
    assert get_res.json()["id"] == emp_id

    # Missing ID
    missing_res = client.get("/employees/9999", headers=auth_header(admin_token))
    assert missing_res.status_code == 404


def test_update_and_delete_employee(admin_token, auth_header, client):
    create_res = client.post(
        "/employees/",
        json=SAMPLE_EMPLOYEE,
        headers=auth_header(admin_token),
    )
    emp_id = create_res.json()["id"]

    # Update
    update_res = client.put(
        f"/employees/{emp_id}",
        json={"salary": 140000.0, "position": "Principal Architect"},
        headers=auth_header(admin_token),
    )
    assert update_res.status_code == 200
    assert update_res.json()["salary"] == 140000.0
    assert update_res.json()["position"] == "Principal Architect"

    # Delete
    del_res = client.delete(f"/employees/{emp_id}", headers=auth_header(admin_token))
    assert del_res.status_code == 204

    # Verify deleted
    get_again = client.get(f"/employees/{emp_id}", headers=auth_header(admin_token))
    assert get_again.status_code == 404


def test_regular_user_read_allowed_write_forbidden(
    admin_token, user_token, auth_header, client
):
    create_res = client.post(
        "/employees/",
        json=SAMPLE_EMPLOYEE,
        headers=auth_header(admin_token),
    )
    emp_id = create_res.json()["id"]

    # Regular user can read
    read_res = client.get("/employees/", headers=auth_header(user_token))
    assert read_res.status_code == 200
    assert len(read_res.json()) == 1

    # Regular user cannot create
    create_forbidden = client.post(
        "/employees/",
        json={**SAMPLE_EMPLOYEE, "email": "forbidden@test.com"},
        headers=auth_header(user_token),
    )
    assert create_forbidden.status_code == 403

    # Regular user cannot update
    update_forbidden = client.put(
        f"/employees/{emp_id}",
        json={"salary": 200000.0},
        headers=auth_header(user_token),
    )
    assert update_forbidden.status_code == 403

    # Regular user cannot delete
    del_forbidden = client.delete(
        f"/employees/{emp_id}",
        headers=auth_header(user_token),
    )
    assert del_forbidden.status_code == 403


def test_unauthenticated_request_rejected(client):
    resp = client.get("/employees/")
    assert resp.status_code == 401


def test_employee_stats_summary(admin_token, auth_header, client):
    # Empty stats
    empty_stats = client.get(
        "/employees/stats/summary", headers=auth_header(admin_token)
    )
    assert empty_stats.status_code == 200
    assert empty_stats.json()["total_employees"] == 0

    # Add employees
    client.post(
        "/employees/",
        json={**SAMPLE_EMPLOYEE, "salary": 100000.0},
        headers=auth_header(admin_token),
    )
    client.post(
        "/employees/",
        json={
            **SAMPLE_EMPLOYEE,
            "email": "another@test.com",
            "department": "Finance",
            "salary": 200000.0,
        },
        headers=auth_header(admin_token),
    )

    stats_res = client.get(
        "/employees/stats/summary", headers=auth_header(admin_token)
    )
    assert stats_res.status_code == 200
    data = stats_res.json()
    assert data["total_employees"] == 2
    assert data["total_departments"] == 2
    assert data["total_payroll"] == 300000.0
    assert data["average_salary"] == 150000.0
