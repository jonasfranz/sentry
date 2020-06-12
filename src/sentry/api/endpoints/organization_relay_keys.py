from __future__ import absolute_import

from copy import deepcopy
from datetime import datetime

from sentry.api.bases import OrganizationEndpoint, OrganizationAdminPermission
from sentry.coreapi import APIForbidden
from sentry import features
from sentry.models.relay import Relay
from rest_framework import status
from rest_framework.response import Response
from sentry.api.serializers.rest_framework.base import (
    snake_to_camel_case,
    camel_to_snake_case,
    convert_dict_key_case,
)

ORG_RELAYS_OPTION = "sentry:trusted_relays"


class OrganizationRelayKeysEndpoint(OrganizationEndpoint):
    # TODO (RaduW) decide exactly on the Authorization model that we want
    # GET=org.read, others org.admin
    # permission_classes = (OrganizationAuthProviderPermission,)
    # all HTTP methods org.admin
    permission_classes = (OrganizationAdminPermission,)

    def check_feature_enabled(self, request, organization):
        if not features.has("organizations:relay-config", organization, actor=request.user):
            raise APIForbidden("Relay configuration is not enabled for this organization.")

    def get(self, request, organization):
        self.check_feature_enabled(request, organization)

        relay_keys = organization.get_option(ORG_RELAYS_OPTION, [])
        public_keys = [key_info.get("public_key") for key_info in relay_keys]
        usage = _get_keys_usage(public_keys)
        ret_val = _add_usage_info(relay_keys, usage)

        return Response(_to_camel(ret_val), status=status.HTTP_200_OK)

    def put(self, request, organization, public_key):
        self.check_feature_enabled(request, organization)
        data = _to_snake(request.json_body)
        relay_keys = organization.get_option(ORG_RELAYS_OPTION, [])

        for existing_key in relay_keys:
            if existing_key.get("public_key") == public_key:
                # the key was already used change the name/description
                existing_key["name"] = data.get("name")
                existing_key["description"] = data.get("description")
                ret_val = existing_key
                break
        else:
            data["public_key"] = public_key
            data["created"] = datetime.utcnow()
            relay_keys.append(data)
            ret_val = data

        organization.update_option(ORG_RELAYS_OPTION, relay_keys)
        return Response(_to_camel(ret_val), status=status.HTTP_200_OK)

    def delete(self, request, organization, public_key):
        self.check_feature_enabled(request, organization)
        old_keys = organization.get_option(ORG_RELAYS_OPTION, [])
        new_keys = [key_info for key_info in old_keys if key_info.get("public_key") != public_key]

        if len(old_keys) == len(new_keys):
            return Response(_error("invalid_relay_key"), status=status.HTTP_404_NOT_FOUND)

        organization.update_option(ORG_RELAYS_OPTION, new_keys)
        return Response(status=status.HTTP_204_NO_CONTENT)


def _add_usage_info(relay_keys, usage_dict):
    def full_key_info(usage_dict, info):
        ret_val = deepcopy(info)
        key = ret_val.get("public_key")
        usage_info = usage_dict.get(key, {})
        for key in ("last_used", "first_used"):
            val = usage_info.get(key)
            if val is not None:
                ret_val[key] = val
        return ret_val

    if relay_keys is None:
        return []

    return [full_key_info(usage_dict, info) for info in relay_keys]


def _relay_key(
    public_key, name, description, created, last_modified=None, first_used=None, last_used=None
):
    ret_val = {"public_key": public_key, "name": name, "created": created}

    if description is not None:
        ret_val["description"] = description

    if last_modified is not None:
        ret_val["last_modified"] = last_modified

    if first_used is not None:
        ret_val["first_used"] = first_used

    if last_used is not None:
        ret_val["last_used"] = last_used

    return ret_val


def _get_keys_usage(keys):
    relays_for_keys = Relay.for_keys(keys)

    ret_val = {}

    for relay in relays_for_keys:
        first_seen = relay.first_seen
        last_seen = relay.last_seen

        existing = ret_val.get(relay.public_key)

        if existing:  # key already seen in previous relay, join its usage
            e_first_seen = existing.get("first_seen")
            if e_first_seen is not None and first_seen is not None:
                first_seen = min(first_seen, e_first_seen)
            elif first_seen is None:
                first_seen = e_first_seen

            e_last_seen = existing.get("last_seen")
            if e_last_seen is not None and last_seen is not None:
                last_seen = max(last_seen, e_last_seen)
            elif last_seen is None:
                last_seen = e_last_seen

        ret_val[relay.public_key] = {"first_seen": first_seen, "last_seen": last_seen}

    return ret_val


def _to_snake(obj):
    return convert_dict_key_case(obj, camel_to_snake_case)


def _to_camel(obj):
    return convert_dict_key_case(obj, snake_to_camel_case)


def _error(error_msg):
    return {"detail": error_msg}
