from __future__ import absolute_import

from sentry.shared_integrations.exceptions import ApiError, IntegrationError
from sentry.plugins import providers
from sentry.models import Integration


class GiteaRepositoryProvider(providers.IntegrationRepositoryProvider):
    name = "gitea"

    def get_installation(self, integration_id, organization_id):
        if integration_id is None:
            raise IntegrationError("%s requires an integration id." % self.name)

        integration_model = Integration.objects.get(
            id=integration_id, organizations=organization_id, provider="gitea"
        )

        return integration_model.get_installation(organization_id)

    def get_repository_data(self, organization, config):
        installation = self.get_installation(config.get("installation"), organization.id)
        client = installation.get_client()

        repo_name = config["identifier"]
        instance = installation.model.metadata["instance"]

        try:
            repo = client.get_repo(repo_name)
        except Exception as e:
            installation.raise_error(e)
        config.update(
            {
                "instance": instance,
                "name": repo_name,
                "external_id": u"{}:{}".format(instance, repo_name),
                "url": repo["html_url"],
                "repo": repo_name,
            }
        )
        return config

    def build_repository_config(self, organization, data):

        installation = self.get_installation(data.get("installation"), organization.id)
        client = installation.get_client()
        hook_id = None
        try:
            hook_id = client.create_repo_webhook(data["repo"])
        except Exception as e:
            installation.raise_error(e)
        return {
            "name": data["name"],
            "external_id": data["external_id"],
            "url": data["url"],
            "config": {"instance": data["instance"], "webhook_id": hook_id, "repo": data["repo"]},
            "integration_id": data["installation"],
        }

    def on_delete_repository(self, repo):
        """Clean up the attached webhook"""
        installation = self.get_installation(repo.integration_id, repo.organization_id)
        client = installation.get_client()
        try:
            client.delete_repo_webhook(repo.config["repo"], repo.config["webhook_id"])
        except ApiError as e:
            if e.code == 404:
                return
            installation.raise_error(e)

    def pull_request_url(self, repo, pull_request):
        return u"{}/pulls/{}".format(repo.url, pull_request.key)

    def repository_external_slug(self, repo):
        return repo.config["repo"]
