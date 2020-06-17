from __future__ import absolute_import

import logging

import six

from sentry import http
from sentry.auth.exceptions import IdentityNotValid
from sentry.http import safe_urlopen, safe_urlread
from sentry.identity.oauth2 import OAuth2Provider
from sentry.utils import json

logger = logging.getLogger("sentry.integration.gitea")


def get_oauth_data(payload):
    data = {"access_token": payload["access_token"]}

    # See https://docs.gitea.io/en-us/oauth2-provider/
    if "refresh_token" in payload:
        data["refresh_token"] = payload["refresh_token"]
    if "token_type" in payload:
        data["token_type"] = payload["token_type"]
    if "expires_in" in payload:
        data["expires_in"] = int(payload["expires_in"])

    return data


def get_user_info(access_token, installation_data):
    session = http.build_session()
    resp = session.get(
        u"{}/api/v1/user".format(installation_data["url"]),
        headers={"Accept": "application/json", "Authorization": "Bearer %s" % access_token},
        verify=installation_data["verify_ssl"],
    )
    try:
        resp.raise_for_status()
    except Exception as e:
        logger.info(
            "gitea.identity.get-user-info-failure",
            extra={
                "url": installation_data["url"],
                "verify_ssl": installation_data["verify_ssl"],
                "client_id": installation_data["client_id"],
                "error_status": e.code,
                "error_message": six.text_type(e),
            },
        )
        raise e
    return resp.json()


class GiteaIdentityProvider(OAuth2Provider):
    key = "gitea"
    name = "Gitea"

    def build_identity(self, data):
        data = data["data"]

        return {
            "type": "gitea",
            "id": data["user"]["id"],
            "email": data["user"]["email"],
            "data": self.get_oauth_data(data),
        }

    def get_refresh_token_params(self, refresh_token, *args, **kwargs):
        return {"grant_type": "refresh_token", "refresh_token": refresh_token}

    def refresh_identity(self, identity, *args, **kwargs):
        refresh_token = identity.data.get("refresh_token")
        refresh_token_url = kwargs.get("refresh_token_url")

        if not refresh_token:
            raise IdentityNotValid("Missing refresh token")

        if not refresh_token_url:
            raise IdentityNotValid("Missing refresh token url")

        data = self.get_refresh_token_params(refresh_token, *args, **kwargs)

        req = safe_urlopen(url=refresh_token_url, headers={}, data=data)

        try:
            body = safe_urlread(req)
            payload = json.loads(body)
        except Exception as e:
            self.logger(
                "gitea.refresh-identity-failure",
                extra={
                    "identity_id": identity.id,
                    "error_status": e.code,
                    "error_message": six.text_type(e),
                },
            )
            payload = {}

        self.handle_refresh_error(req, payload)

        identity.data.update(get_oauth_data(payload))
        return identity.update(data=identity.data)
