from bitmask import Bitmask
from sachet.server.models import Permissions, ServerSettings

server_settings_schema = ServerSettings.get_schema(ServerSettings)


def test_default_perms(client, tokens):
    """Test the default permissions."""

    # try with regular user to make sure it doesn't work
    resp = client.get(
        "/admin/settings",
        headers={"Authorization": f"bearer {tokens['jeff']}"},
    )
    assert resp.status_code == 403

    resp = client.get(
        "/admin/settings",
        headers={"Authorization": f"bearer {tokens['administrator']}"},
    )
    assert resp.status_code == 200

    assert server_settings_schema.load(resp.get_json()) == dict(
        default_permissions=Bitmask(AllFlags=Permissions)
    )


def test_patch_perms(client, tokens):
    """Test the PATCH endpoint for default server permissions."""

    # try with regular user to make sure it doesn't work
    resp = client.patch(
        "/admin/settings",
        json={"default_permissions": ["ADMIN"]},
        headers={"Authorization": f"bearer {tokens['jeff']}"},
    )
    assert resp.status_code == 403

    # test malformed patch
    resp = client.patch(
        "/admin/settings",
        json="hurr durr",
        headers={"Authorization": f"bearer {tokens['administrator']}"},
    )
    assert resp.status_code == 400

    resp = client.patch(
        "/admin/settings",
        json={"default_permissions": ["ADMIN"]},
        headers={"Authorization": f"bearer {tokens['administrator']}"},
    )
    assert resp.status_code == 200

    # request new info
    resp = client.get(
        "/admin/settings",
        headers={"Authorization": f"bearer {tokens['administrator']}"},
    )
    assert resp.status_code == 200

    assert server_settings_schema.load(resp.get_json()) == dict(
        default_permissions=Bitmask(Permissions.ADMIN)
    )


def test_put_perms(client, tokens):
    """Test the PUT endpoint for default server permissions."""

    # try with regular user to make sure it doesn't work
    resp = client.put(
        "/admin/settings",
        json={"default_permissions": ["ADMIN"]},
        headers={"Authorization": f"bearer {tokens['jeff']}"},
    )
    assert resp.status_code == 403

    # test malformed put
    resp = client.put(
        "/admin/settings",
        json="hurr durr",
        headers={"Authorization": f"bearer {tokens['administrator']}"},
    )
    assert resp.status_code == 400

    # request current info (that we'll modify before putting back)
    resp = client.get(
        "/admin/settings",
        headers={"Authorization": f"bearer {tokens['administrator']}"},
    )
    assert resp.status_code == 200

    data = resp.get_json()
    data["default_permissions"] = ["ADMIN"]

    resp = client.put(
        "/admin/settings",
        json=data,
        headers={"Authorization": f"bearer {tokens['administrator']}"},
    )
    assert resp.status_code == 200

    # request new info
    resp = client.get(
        "/admin/settings",
        headers={"Authorization": f"bearer {tokens['administrator']}"},
    )
    assert resp.status_code == 200

    assert server_settings_schema.load(resp.get_json()) == dict(
        default_permissions=Bitmask(Permissions.ADMIN)
    )
