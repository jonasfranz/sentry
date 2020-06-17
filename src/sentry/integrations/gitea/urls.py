from __future__ import absolute_import, print_function

from django.conf.urls import url

from .webhooks import GitlabWebhookEndpoint
from .search import GiteaIssueSearchEndpoint

urlpatterns = [
    url(
        r"^search/(?P<organization_slug>[^\/]+)/(?P<integration_id>\d+)/$",
        GiteaIssueSearchEndpoint.as_view(),
        name="sentry-extensions-gitea-search",
    ),
    url(r"^webhook/$", GitlabWebhookEndpoint.as_view(), name="sentry-extensions-gitea-webhook"),
]
