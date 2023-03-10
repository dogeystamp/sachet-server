import pytest
import jwt
from sachet.server import db
from sachet.server.users import manage

def test_reserved_users(client):
    """Test that the server prevents reserved endpoints from being registered as usernames."""
    for user in ["login", "logout", "extend"]:
        with pytest.raises(KeyError):
            manage.create_user(False, user, "")

def test_unauth_perms(client):
    """Test endpoints to see if they allow unauthenticated users."""
    resp = client.get("/users/jeff")
    assert resp.status_code == 401

def test_malformed_authorization(client):
    """Test attempting authorization incorrectly."""

    # incorrect token
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    resp = client.get(
        "/users/jeff",
        headers={
            "Authorization": f"bearer {token}"
        }
    )
    assert resp.status_code == 401

    # token for incorrect user (but properly signed)
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.nZ86hUWPdG43W6HVSGFy6DJnDVOZhx8a73LhQ3gIxY8"
    resp = client.get(
        "/users/jeff",
        headers={
            "Authorization": f"bearer {token}"
        }
    )
    assert resp.status_code == 401

    # invalid token
    token = "not a.real JWT.token"
    resp = client.get(
        "/users/jeff",
        headers={
            "Authorization": f"bearer {token}"
        }
    )
    assert resp.status_code == 401

    # missing token
    resp = client.get(
        "/users/jeff",
        headers={
            "Authorization": "bearer"
        }
    )
    assert resp.status_code == 401

def test_login(client, users):
    """Test logging in."""

    # wrong password
    resp = client.post("/users/login", json={
        "username": "jeff",
        "password": users["jeff"]["password"] + "garbage"
    })
    assert resp.status_code == 401

    # wrong user
    resp = client.post("/users/login", json={
        "username": "jeffery",
        "password": users["jeff"]["password"] + "garbage"
    })
    assert resp.status_code == 401

    # logging in correctly
    resp = client.post("/users/login", json={
        "username": "jeff",
        "password": users["jeff"]["password"]
    })
    assert resp.status_code == 200
    resp_json = resp.get_json()
    assert resp_json.get("status") == "success"
    assert resp_json.get("username") == "jeff"
    token = resp_json.get("auth_token")
    assert token is not None and token != ""
