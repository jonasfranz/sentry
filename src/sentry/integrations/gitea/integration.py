from __future__ import absolute_import

import six
from six.moves.urllib.parse import urlparse
from django.utils.translation import ugettext_lazy as _
from django import forms

from sentry.web.helpers import render_to_response
from sentry.identity.pipeline import IdentityProviderPipeline
from sentry.identity.gitea import get_user_info, get_oauth_data
from sentry.integrations import (
    FeatureDescription,
    IntegrationInstallation,
    IntegrationFeatures,
    IntegrationProvider,
    IntegrationMetadata,
)
from sentry.shared_integrations.exceptions import ApiError, IntegrationError
from sentry.integrations.repositories import RepositoryMixin
from sentry.pipeline import NestedPipelineView, PipelineView
from sentry.utils.http import absolute_uri
from sentry.utils.hashlib import sha1_text

from .client import GiteaApiClient, GiteaSetupClient
from .issues import GiteaIssueBasic
from .repository import GiteaRepositoryProvider

DESCRIPTION = """
Connect your Sentry organization to an organization or user in your Gitea instance or gitea.com, enabling the following features:
"""

FEATURES = [
    FeatureDescription(
        """
        Track commits and releases (learn more
        [here](https://docs.sentry.io/learn/releases/))
        """,
        IntegrationFeatures.COMMITS,
    ),
    FeatureDescription(
        """
        Resolve Sentry issues via Gitea commits and pull requests by
        including `Fixes PROJ-ID` in the message
        """,
        IntegrationFeatures.COMMITS,
    ),
    FeatureDescription(
        """
        Create Gitea issues from Sentry
        """,
        IntegrationFeatures.ISSUE_BASIC,
    ),
    FeatureDescription(
        """
        Link Sentry issues to existing Gitea issues
        """,
        IntegrationFeatures.ISSUE_BASIC,
    ),
]

metadata = IntegrationMetadata(
    description=DESCRIPTION.strip(),
    features=FEATURES,
    author="Jonas Franz",
    noun=_("Installation"),
    issue_url="https://github.com/getsentry/sentry/issues/",
    source_url="https://github.com/getsentry/sentry/tree/master/src/sentry/integrations/gitea",
    aspects={},
)


class GiteaIntegration(IntegrationInstallation, GiteaIssueBasic, RepositoryMixin):
    repo_search = False

    def __init__(self, *args, **kwargs):
        super(GiteaIntegration, self).__init__(*args, **kwargs)
        self.default_identity = None

    def get_client(self):
        if self.default_identity is None:
            self.default_identity = self.get_default_identity()

        return GiteaApiClient(self)

    def get_repositories(self, query=None):
        # query is not supported by gitea
        resp = self.get_client().search_repos()
        return [{"identifier": repo["full_name"], "name": repo["full_name"]} for repo in resp]

    # TODO support Gitea
    def search_projects(self, query):
        client = self.get_client()
        group_id = self.get_group_id()
        return client.search_group_projects(group_id, query)

    def search_issues(self, repo, query):
        client = self.get_client()
        return client.search_repo_issues(repo, query)


class InstallationForm(forms.Form):
    url = forms.CharField(
        label=_("Gitea URL"),
        help_text=_(
            "The base URL for your Gitea instance, including the host and protocol. "
            "Do not include user/organization path."
            "<br>"
            "If using gitea.com, enter https://gitea.com/"
        ),
        widget=forms.TextInput(attrs={"placeholder": "https://gitea.example.com"}),
    )
    verify_ssl = forms.BooleanField(
        label=_("Verify SSL"),
        help_text=_(
            "By default, we verify SSL certificates "
            "when delivering payloads to your Gitea instance."
        ),
        widget=forms.CheckboxInput(),
        required=False,
        initial=True,
    )
    client_id = forms.CharField(
        label=_("Gitea OAuth2 Application Client ID"),
        widget=forms.TextInput(attrs={"placeholder": _("61f54510-38f6-4627-b4d8-780cd7e7f6cd")}),
    )
    client_secret = forms.CharField(
        label=_("Gitea OAuth2 Application Client Secret"),
        widget=forms.TextInput(attrs={"placeholder": _("XXXXXXXXXXXXXXXXXXXXXXXXXXX")}),
    )

    def clean_url(self):
        """Strip off trailing / as they cause invalid URLs downstream"""
        return self.cleaned_data["url"].rstrip("/")


class InstallationConfigView(PipelineView):
    def dispatch(self, request, pipeline):
        if "goback" in request.GET:
            pipeline.state.step_index = 0
            return pipeline.current_step()

        if request.method == "POST":
            form = InstallationForm(request.POST)
            if form.is_valid():
                form_data = form.cleaned_data

                pipeline.bind_state("installation_data", form_data)

                pipeline.bind_state(
                    "oauth_config_information",
                    {
                        "access_token_url": u"{}/login/oauth/access_token".format(
                            form_data.get("url")
                        ),
                        "authorize_url": u"{}/login/oauth/authorize".format(form_data.get("url")),
                        "client_id": form_data.get("client_id"),
                        "client_secret": form_data.get("client_secret"),
                        "verify_ssl": form_data.get("verify_ssl"),
                    },
                )
                pipeline.get_logger().info(
                    "gitea.setup.installation-config-view.success",
                    extra={
                        "base_url": form_data.get("url"),
                        "client_id": form_data.get("client_id"),
                        "verify_ssl": form_data.get("verify_ssl"),
                    },
                )
                return pipeline.next_step()
        else:
            form = InstallationForm()

        return render_to_response(
            template="sentry/integrations/gitea-config.html",
            context={"form": form},
            request=request,
        )


class InstallationGuideView(PipelineView):
    def dispatch(self, request, pipeline):
        if "completed_installation_guide" in request.GET:
            return pipeline.next_step()
        return render_to_response(
            template="sentry/integrations/gitea-config.html",
            context={
                "next_url": "%s%s"
                % (absolute_uri("extensions/gitea/setup/"), "?completed_installation_guide"),
                "setup_values": [
                    {"label": "Application Name", "value": "Sentry"},
                    {"label": "Redirect URI", "value": absolute_uri("/extensions/gitea/setup/")},
                ],
            },
            request=request,
        )


class GiteaIntegrationProvider(IntegrationProvider):
    key = "gitea"
    name = "Gitea"
    metadata = metadata
    integration_cls = GiteaIntegration

    needs_default_identity = True

    features = frozenset([IntegrationFeatures.ISSUE_BASIC, IntegrationFeatures.COMMITS])

    setup_dialog_config = {"width": 1030, "height": 1000}

    def _make_identity_pipeline_view(self):
        """
        Make the nested identity provider view. It is important that this view is
        not constructed until we reach this step and the
        ``oauth_config_information`` is available in the pipeline state. This
        method should be late bound into the pipeline vies.
        """
        identity_pipeline_config = dict(
            redirect_url=absolute_uri("/extensions/gitea/setup/"),
            **self.pipeline.fetch_state("oauth_config_information")
        )

        return NestedPipelineView(
            bind_key="identity",
            provider_key="gitea",
            pipeline_cls=IdentityProviderPipeline,
            config=identity_pipeline_config,
        )

    def get_user_info(self, access_token, installation_data):
        client = GiteaSetupClient(
            installation_data["url"], access_token, installation_data["verify_ssl"]
        )
        try:
            resp = client.get_user()
            return resp.json
        except ApiError as e:
            self.get_logger().info(
                "gitea.installation.get-user-info-failure",
                extra={
                    "base_url": installation_data["url"],
                    "verify_ssl": installation_data["verify_ssl"],
                    "error_message": six.text_type(e),
                    "error_status": e.code,
                },
            )
            raise IntegrationError("The requested Gitea user could not be found.")

    def get_pipeline_views(self):
        return [
            InstallationGuideView(),
            InstallationConfigView(),
            lambda: self._make_identity_pipeline_view(),
        ]

    def build_integration(self, state):
        data = state["identity"]["data"]
        oauth_data = get_oauth_data(data)
        user = get_user_info(data["access_token"], state["installation_data"])
        base_url = state["installation_data"]["url"]

        hostname = urlparse(base_url).netloc
        verify_ssl = state["installation_data"]["verify_ssl"]

        # Generate a hash to prevent stray hooks from being accepted
        # use a consistent hash so that reinstalls/shared integrations don't
        # rotate secrets.
        secret = sha1_text("".join([hostname, state["installation_data"]["client_id"]]))

        integration = {
            "name": user["username"],
            # Splice the gitea host and project together to
            # act as unique link between a gitea instance, user + sentry.
            # This value is embedded then in the webhook token that we
            # give to gitea to allow us to find the integration a hook came
            # from.
            "external_id": u"{}:{}".format(hostname, user["id"]),
            "metadata": {
                "icon": user["avatar_url"],
                "instance": hostname,
                "domain_name": u"{}/{}".format(hostname, user["username"]),
                "verify_ssl": verify_ssl,
                "base_url": base_url,
                "webhook_secret": secret.hexdigest(),
                "user_id": user["id"],
            },
            "user_identity": {
                "type": "gitea",
                "external_id": u"{}:{}".format(hostname, user["id"]),
                "data": oauth_data,
                "scopes": [],
            },
        }
        return integration

    def setup(self):
        from sentry.plugins.base import bindings

        # TODO
        bindings.add(
            "integration-repository.provider", GiteaRepositoryProvider, id="integrations:gitea"
        )
