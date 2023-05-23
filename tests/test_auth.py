import pytest
import jwt
from sachet.server import db
from sachet.server.users import manage


def test_unauth_perms(client):
    """Test endpoints to see if they allow unauthenticated users."""
    resp = client.get("/users/jeff")
    assert resp.status_code == 401


def test_malformed_authorization(client):
    """Test attempting authorization incorrectly."""

    # incorrect token
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    resp = client.get("/users/jeff", headers={"Authorization": f"bearer {token}"})
    assert resp.status_code == 401

    # token for incorrect user (but properly signed)
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.nZ86hUWPdG43W6HVSGFy6DJnDVOZhx8a73LhQ3gIxY8"
    resp = client.get("/users/jeff", headers={"Authorization": f"bearer {token}"})
    assert resp.status_code == 401

    # invalid token
    token = "not a.real JWT.token"
    resp = client.get("/users/jeff", headers={"Authorization": f"bearer {token}"})
    assert resp.status_code == 401

    # missing token
    resp = client.get("/users/jeff", headers={"Authorization": "bearer"})
    assert resp.status_code == 401


def test_login(client, users):
    """Test logging in."""

    # wrong password
    resp = client.post(
        "/users/login",
        json={"username": "jeff", "password": users["jeff"]["password"] + "garbage"},
    )
    assert resp.status_code == 401

    # wrong user
    resp = client.post(
        "/users/login",
        json={"username": "jeffery", "password": users["jeff"]["password"] + "garbage"},
    )
    assert resp.status_code == 401

    # logging in correctly
    resp = client.post(
        "/users/login", json={"username": "jeff", "password": users["jeff"]["password"]}
    )
    assert resp.status_code == 200
    resp_json = resp.get_json()
    assert resp_json.get("status") == "success"
    assert resp_json.get("username") == "jeff"
    token = resp_json.get("auth_token")
    assert token is not None and token != ""


def test_extend(client, tokens, validate_info, auth):
    """Test extending the token lifespan (get a new one with later expiry)."""

    # obtain new token
    resp = client.post("/users/extend", headers=auth("jeff"))
    assert resp.status_code == 200
    resp_json = resp.get_json()
    new_token = resp_json.get("auth_token")
    assert new_token is not None
    assert new_token is not tokens["jeff"]

    # revoke old token

    resp = client.post(
        "/users/logout",
        json={"token": tokens["jeff"]},
        headers=auth("jeff"),
    )

    # log in with the new token
    resp = client.get("/users/jeff", headers={"Authorization": f"Bearer {new_token}"})
    assert resp.status_code == 200
    resp_json = resp.get_json()
    validate_info("jeff", resp_json)


def test_logout(client, tokens, validate_info, auth):
    """Test logging out."""

    # unauthenticated
    resp = client.post(
        "/users/logout",
        json={"token": tokens["jeff"]},
    )
    assert resp.status_code == 401

    # missing token
    resp = client.post("/users/logout", json={}, headers=auth("jeff"))
    assert resp.status_code == 400

    # invalid token
    resp = client.post(
        "/users/logout",
        json={"token": "not.real.jwt"},
        headers=auth("jeff"),
    )
    assert resp.status_code == 400

    # wrong user's token
    resp = client.post(
        "/users/logout",
        json={"token": tokens["administrator"]},
        headers=auth("jeff"),
    )
    assert resp.status_code == 403

    # check that we can access this endpoint before logging out
    resp = client.get("/users/jeff", headers=auth("jeff"))
    assert resp.status_code == 200
    validate_info("jeff", resp.get_json())

    # valid logout
    resp = client.post(
        "/users/logout",
        json={"token": tokens["jeff"]},
        headers=auth("jeff"),
    )
    assert resp.status_code == 200

    # check that the logout worked

    resp = client.get("/users/jeff", headers=auth("jeff"))
    assert resp.status_code == 401


def test_password_change(client, tokens, users, auth):
    """Test changing passwords."""

    # test that we're logged in
    resp = client.get("/users/jeff", headers=auth("jeff"))
    assert resp.status_code == 200

    # change password
    resp = client.post(
        "/users/password",
        json=dict(old=users["jeff"]["password"], new="new_password"),
        headers=auth("jeff"),
    )
    assert resp.status_code == 200

    # revoke old token
    resp = client.post(
        "/users/logout", json=dict(token=tokens["jeff"]), headers=auth("jeff")
    )
    assert resp.status_code == 200

    # test that we're logged out
    resp = client.get(
        "/users/jeff", headers=auth("jeff"), json=dict(token=tokens["jeff"])
    )
    assert resp.status_code == 401

    # sign in with new token
    resp = client.post(
        "/users/login", json=dict(username="jeff", password="new_password")
    )
    assert resp.status_code == 200
    data = resp.get_json()
    new_token = data.get("auth_token")
    assert new_token

    # test that we're logged in
    resp = client.get("/users/jeff", headers=dict(Authorization=f"bearer {new_token}"))
    assert resp.status_code == 200


def test_admin_revoke(client, tokens, validate_info, auth):
    """Test that an admin can revoke any token from other users."""

    resp = client.post(
        "/users/logout",
        json={"token": tokens["jeff"]},
        headers=auth("administrator"),
    )
    assert resp.status_code == 200

    # check that the logout worked

    resp = client.get("/users/jeff", headers=auth("jeff"))
    assert resp.status_code == 401

    # try revoking twice

    resp = client.post(
        "/users/logout",
        json={"token": tokens["jeff"]},
        headers=auth("administrator"),
    )
    assert resp.status_code == 400
