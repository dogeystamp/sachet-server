import pytest

def test_userinfo(client, tokens, validate_info):
    """Test accessing the user information endpoint as a normal user."""

    # access user info endpoint
    resp = client.get(
        "/users/jeff",
        headers={
            "Authorization": f"bearer {tokens['jeff']}"
        }
    )
    assert resp.status_code == 200
    validate_info("jeff", resp.get_json())


    # access other user's info endpoint
    resp = client.get(
        "/users/administrator",
        headers={
            "Authorization": f"bearer {tokens['jeff']}"
        }
    )
    assert resp.status_code == 403

def test_userinfo_admin(client, tokens, validate_info):
    """Test accessing other user's information as an admin."""

    # first test that admin can access its own info
    resp = client.get(
        "/users/administrator",
        headers={
            "Authorization": f"bearer {tokens['administrator']}"
        }
    )
    assert resp.status_code == 200
    validate_info("administrator", resp.get_json())

    # now test accessing other user's info
    resp = client.get(
        "/users/jeff",
        headers={
            "Authorization": f"bearer {tokens['administrator']}"
        }
    )
    assert resp.status_code == 200
    validate_info("jeff", resp.get_json())
