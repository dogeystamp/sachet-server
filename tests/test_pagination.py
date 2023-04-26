import pytest
from math import ceil
import json

"""Test ability to paginate endpoint responses."""


def test_files(client, users, auth):
    """Test /files endpoint."""

    # create multiple shares
    shares = set()
    share_count = 20

    for i in range(share_count):
        resp = client.post(
            "/files", headers=auth("jeff"), json={"file_name": "content.bin"}
        )
        assert resp.status_code == 201
        data = resp.get_json()
        share_id = data.get("url").split("/")[-1]
        shares.add(share_id)

    # we'll paginate through all shares and ensure that:
    # - we see all the shares
    # - no shares are seen twice

    def paginate(forwards=True, page=1):
        """Goes through the pages.

        Parameters
        ----------
        forwards : bool, optional
            Set direction to paginate in.
        page : int
            Page to start at.

        Returns
        -------
        int
            Page we ended at.
        """
        seen = set()

        per_page = 9
        while page is not None:
            resp = client.get(
                "/files", headers=auth("jeff"), json=dict(
                    page=page,
                    per_page=per_page
                )
            )
            assert resp.status_code == 200

            data = resp.get_json().get("data")
            assert len(data) == per_page or len(data) == share_count % per_page

            for share in data:
                share_id = share.get("share_id")
                assert share_id in shares
                assert share_id not in seen
                seen.add(share_id)

            if forwards:
                new_page = resp.get_json().get("next")
                assert new_page == page + 1 or new_page is None
            else:
                new_page = resp.get_json().get("prev")
                assert new_page == page - 1 or new_page is None
            if new_page is not None:
                page = new_page
            else:
                break

        assert seen == shares

        return page

    end_page = paginate(forwards=True)
    paginate(forwards=False, page=end_page)
