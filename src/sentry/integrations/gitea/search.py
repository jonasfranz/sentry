from __future__ import absolute_import

from rest_framework.response import Response

from sentry.api.bases.integration import IntegrationEndpoint
from sentry.shared_integrations.exceptions import ApiError
from sentry.models import Integration


class GiteaIssueSearchEndpoint(IntegrationEndpoint):
    def get(self, request, organization, integration_id):
        try:
            integration = Integration.objects.get(organizations=organization, id=integration_id)
        except Integration.DoesNotExist:
            return Response(status=404)

        field = request.GET.get("field")
        query = request.GET.get("query")
        if field is None:
            return Response({"detail": "field is a required parameter"}, status=400)
        if not query:
            return Response({"detail": "query is a required parameter"}, status=400)

        installation = integration.get_installation(organization.id)
        if field == "externalIssue":
            repo = request.GET.get("repo")
            if repo is None:
                return Response({"detail": "repo is a required parameter"}, status=400)

            try:
                response = installation.search_issues(query=query.encode("utf-8"), repo=repo)
            except ApiError as err:
                if err.code == 403:
                    return Response({"detail": "Rate limit exceeded"}, status=429)
                raise
            return Response(
                [
                    {"label": "#%s %s" % (i["number"], i["title"]), "value": i["number"]}
                    for i in response
                ]
            )

        return Response(status=400)
