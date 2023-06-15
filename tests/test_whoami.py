"""Test /whoami."""


def test_whoami(client, auth):
    """Test authenticated whoami."""

    for perms in [["READ"], ["CREATE", "MODIFY"], []]:
        resp = client.patch(
            "/users/jeff", headers=auth("administrator"), json=dict(permissions=perms)
        )
        assert resp.status_code == 200
        resp = client.get("/whoami", headers=auth("jeff"))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data.get("username") == "jeff"
        assert data.get("permissions") == perms


def test_anon_whoami(client, auth):
    """Test anonymous whoami."""

    for perms in [["READ"], ["CREATE", "MODIFY"], []]:
        resp = client.patch(
            "/admin/settings",
            headers=auth("administrator"),
            json=dict(default_permissions=perms),
        )
        assert resp.status_code == 200
        resp = client.get("/whoami")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data.get("username") is None
        assert data.get("permissions") == perms
