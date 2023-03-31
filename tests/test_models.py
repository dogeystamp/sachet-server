from sachet.server.models import patch


def test_patch():
    """Tests sachet/server/models.py's patch() method for dicts."""

    assert patch(dict(), dict()) == dict()

    assert patch(dict(key="value"), dict()) == dict(key="value")

    assert patch(dict(key="value"), dict(key="newvalue")) == dict(key="newvalue")

    assert patch(dict(key="value"), dict(key="newvalue")) == dict(key="newvalue")

    assert patch(dict(key="value"), dict(key2="other_value")) == dict(
        key="value", key2="other_value"
    )

    assert patch(
        dict(nest=dict(key="value", key2="other_value")),
        dict(top_key="newvalue", nest=dict(key2="new_other_value")),
    ) == dict(top_key="newvalue", nest=dict(key="value", key2="new_other_value"))

    assert patch(
        dict(nest=dict(key="value", list=[1, 2, 3, 4, 5])),
        dict(top_key="newvalue", nest=dict(list=[3, 1, 4, 1, 5])),
    ) == dict(top_key="newvalue", nest=dict(key="value", list=[3, 1, 4, 1, 5]))
