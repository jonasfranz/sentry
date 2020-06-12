from __future__ import absolute_import
from sentry.api.endpoints.organization_relay_keys import ORG_RELAYS_OPTION
from sentry.models.apitoken import ApiToken
from sentry.testutils import APITestCase

from django.core.urlresolvers import reverse
from datetime import datetime

from sentry.utils import json


class OrganizationReleaseAssembleTest(APITestCase):
    def setUp(self):
        self.organization = self.create_organization(owner=self.user)

        # relay keys api require 'org:admin' rights
        self.good_rights = ApiToken.objects.create(
            user=self.user, scope_list=["org:admin", "org:read", "org:write"]
        )
        self.bad_rights = ApiToken.objects.create(user=self.user, scope_list=["porject:rights"])

        self.pk1 = u"JOaR2bHZ31zYjFojC7UhPOidzfT3qOQgT9WEBw1JAKU"
        self.pk1_first_used = datetime(2019, 10, 1)
        self.pk1_last_used = datetime(2020, 3, 22)
        self.pk1_created = datetime(2020, 6, 11)
        self.pk1_last_modified = datetime(2020, 7, 11)

        self.pk2 = u"SMSesqan65THCV6M4qs4kBzPai60LzuDn-xNsvYpuP8"
        self.pk2_first_used = datetime(2019, 10, 2)
        self.pk2_last_used = datetime(2020, 3, 23)
        self.pk2_created = datetime(2020, 6, 12)
        self.pk2_last_modified = datetime(2020, 7, 12)

        self.create_relay(
            relay_id="rel_1",
            public_key=self.pk1,
            first_seen=self.pk1_first_used,
            last_seen=self.pk1_last_used,
            is_internal=False,
        )
        self.create_relay(
            relay_id="rel_2",
            public_key=self.pk2,
            first_seen=self.pk2_first_used,
            last_seen=self.pk2_last_used,
            is_internal=False,
        )

        keys = [
            {
                "public_key": self.pk1,
                "description": "pk 1 def",
                "name": "pk 1",
                "created": self.pk1_created,
                "last_modified": self.pk1_last_modified,
            },
            {
                "public_key": self.pk2,
                "description": "pk 2 def",
                "name": "pk 2",
                "created": self.pk2_created,
                "last_modified": self.pk2_last_modified,
            },
        ]

        self.organization.update_option(ORG_RELAYS_OPTION, keys)

    def test_get_endpoint_checks_rights(self):
        """
        Tests that the get endpoint only permits properly authorized callers
        """
        with self.feature("organizations:relay-config"):
            url = self._keys_url()
            response = self.client.get(
                url, HTTP_AUTHORIZATION=_authorization_header(self.bad_rights)
            )
            assert response.status_code == 403
            response = self.client.get(
                url, HTTP_AUTHORIZATION=_authorization_header(self.good_rights)
            )
            assert response.status_code == 200

    def test_put_endpoint_checks_rights(self):
        """
        Tests that the put endpoint only permits properly authorized callers
        """
        with self.feature("organizations:relay-config"):
            url = self._key_url("abc")
            data = {"name": "new name", "description": "new description"}
            response = self.client.put(
                url, data=data, HTTP_AUTHORIZATION=_authorization_header(self.bad_rights)
            )
            assert response.status_code == 403
            response = self.client.put(
                url, data=data, HTTP_AUTHORIZATION=_authorization_header(self.good_rights)
            )
            assert response.status_code == 201

    def test_delete_endpoint_checks_rights(self):
        """
        Tests that the delete endpoint only permits properly authorized callers
        """
        with self.feature("organizations:relay-config"):
            url = self._key_url(self.pk1)
            response = self.client.delete(
                url, HTTP_AUTHORIZATION=_authorization_header(self.bad_rights)
            )
            assert response.status_code == 403
            response = self.client.delete(
                url, HTTP_AUTHORIZATION=_authorization_header(self.good_rights)
            )
            assert response.status_code == 204

    def test_get(self):
        """
        Test that the get endpoint returns the existing key configurations
        """
        with self.feature("organizations:relay-config"):
            url = self._keys_url()
            response = self.client.get(
                url, HTTP_AUTHORIZATION=_authorization_header(self.good_rights)
            )
        assert response.status_code == 200

        data = json.loads(response.content)
        assert len(data) == 2

        if data[0].get("name") == "pk 1":
            p1 = data[0]
            p2 = data[1]
        else:
            p1 = data[1]
            p2 = data[0]

        assert _matches_date(self.pk1_first_used, p1.get("firstUsed"))
        assert _matches_date(self.pk1_last_used, p1.get("lastUsed"))
        assert _matches_date(self.pk1_created, p1.get("created"))
        assert "pk 1" == p1.get("name")
        assert "pk 1 def" == p1.get("description")

        assert _matches_date(self.pk2_first_used, p2.get("firstUsed"))
        assert _matches_date(self.pk2_last_used, p2.get("lastUsed"))
        assert _matches_date(self.pk2_created, p2.get("created"))
        assert "pk 2" == p2.get("name")
        assert "pk 2 def" == p2.get("description")

    def test_modify_existing_key(self):
        """
        Test that modifying existing key works
        """
        url = self._key_url(self.pk1)
        data = {"name": "new name", "description": "new description"}

        with self.feature("organizations:relay-config"):
            response = self.client.put(
                url, data=data, HTTP_AUTHORIZATION=_authorization_header(self.good_rights)
            )
            assert response.status_code == 200
            response = self.client.get(
                self._keys_url(), HTTP_AUTHORIZATION=_authorization_header(self.good_rights)
            )
            assert response.status_code == 200

        data = json.loads(response.content)
        assert len(data) == 2

        if data[0].get("publicKey") == self.pk1:
            p = data[0]
        else:
            p = data[1]

        assert p.get("name") == "new name"
        assert p.get("description") == "new description"
        assert not _matches_date(
            self.pk1_last_modified, p.get("lastModified")
        )  # the modified changed

    def test_add_new_key(self):
        """
        Tests that we can add a new key
        """
        pub_key = "some_pub_key"
        url = self._key_url(pub_key)
        data = {"name": "new name", "description": "new description"}

        with self.feature("organizations:relay-config"):
            response = self.client.put(
                url, data=data, HTTP_AUTHORIZATION=_authorization_header(self.good_rights)
            )
            assert response.status_code == 201
            response = self.client.get(
                self._keys_url(), HTTP_AUTHORIZATION=_authorization_header(self.good_rights)
            )
            assert response.status_code == 200

        data = json.loads(response.content)
        assert len(data) == 3

        if data[0].get("publicKey") == pub_key:
            p = data[0]
        elif data[1].get("publicKey") == pub_key:
            p = data[1]
        else:
            p = data[2]

        assert p.get("name") == "new name"
        assert p.get("description") == "new description"

    def test_delete_key(self):
        """
        Tests that we can delete a key
        """
        url = self._key_url(self.pk1)
        data = {"name": "new name", "description": "new description"}

        with self.feature("organizations:relay-config"):
            response = self.client.delete(
                url, data=data, HTTP_AUTHORIZATION=_authorization_header(self.good_rights)
            )
            assert response.status_code == 204
            response = self.client.get(
                self._keys_url(), HTTP_AUTHORIZATION=_authorization_header(self.good_rights)
            )
            assert response.status_code == 200

        data = json.loads(response.content)
        assert len(data) == 1

        p = data[0]
        assert p.get("publicKey") == self.pk2

    def _keys_url(self):
        return reverse("sentry-api-0-organization-relay-keys", args=[self.organization.slug],)

    def _key_url(self, public_key):
        return reverse(
            "sentry-api-0-organization-relay-key", args=[self.organization.slug, public_key],
        )


def _matches_date(the_date, the_string):
    """
    Test if the date part of a date or datetime matches the date part of
    a string formated as YYYY-MM-DDT
    """
    if the_date is None and the_string is None:
        return True
    if the_date is None or the_string is None:
        return False

    as_str = the_date.strftime("%Y-%m-%dT")

    return the_string.startswith(as_str)


def _authorization_header(token):
    return u"Bearer {}".format(token)


def _add_auth_header(headers, token):
    headers["Authorization"] = "Bearer {}".format(token)
    return headers
