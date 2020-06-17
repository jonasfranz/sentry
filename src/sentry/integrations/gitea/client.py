from __future__ import absolute_import

from django.core.urlresolvers import reverse

from sentry.integrations.client import ApiClient
from sentry.shared_integrations.exceptions import ApiError, ApiUnauthorized
from sentry.utils.http import absolute_uri

API_VERSION = u"/api/v1"


class GiteaApiClientPath(object):
    oauth_token = u"/login/oauth/access_token"
    commits = u"/repos/{repo}/commits"
    user_repos = u"/user/repos"
    issue = u"/repos/{repo}/issues/{index}"
    issues = u"/repos/{repo}/issues"
    comments = u"/repos/{repo}/issues/{index}/comments"
    repo = u"/repos/{repo}"
    repo_hooks = u"/repos/{repo}/hooks"
    repo_hook = u"/repos/{repo}/hooks/{id}"
    user = u"/user"

    @staticmethod
    def build_api_url(base_url, path):
        return u"{base_url}{api}{path}".format(base_url=base_url, api=API_VERSION, path=path)


class GiteaSetupClient(ApiClient):
    """
    API Client that doesn't require an installation.
    This client is used during integration setup to fetch data
    needed to build installation metadata
    """

    integration_name = "gitea_setup"

    def __init__(self, base_url, access_token, verify_ssl):
        self.base_url = base_url
        self.token = access_token
        self.verify_ssl = verify_ssl

    def request(self, method, path, data=None, params=None):
        headers = {"Authorization": u"Bearer {}".format(self.token)}
        return self._request(
            method,
            GiteaApiClientPath.build_api_url(self.base_url, path),
            headers=headers,
            data=data,
            params=params,
        )

    def get_user(self):
        """Get a user

        See https://gitea.com/api/v1/swagger#/user/userGetCurrent
        """
        return self.get(GiteaApiClientPath.user)


class GiteaApiClient(ApiClient):
    integration_name = "gitea"

    def __init__(self, installation):
        self.installation = installation
        verify_ssl = self.metadata["verify_ssl"]
        self.is_refreshing_token = False
        super(GiteaApiClient, self).__init__(verify_ssl)

    @property
    def identity(self):
        return self.installation.default_identity

    @property
    def metadata(self):
        return self.installation.model.metadata

    def request(self, method, path, data=None, params=None):
        access_token = self.identity.data["access_token"]
        headers = {"Authorization": u"Bearer {}".format(access_token)}
        url = GiteaApiClientPath.build_api_url(self.metadata["base_url"], path)
        try:
            return self._request(method, url, headers=headers, data=data, params=params)
        except ApiUnauthorized as e:
            if self.is_refreshing_token:
                raise e
            self.is_refreshing_token = True
            self.refresh_auth()
            resp = self._request(method, url, headers=headers, data=data, params=params)
            self.is_refreshing_token = False
            return resp

    def refresh_auth(self):
        self.identity.get_provider().refresh_identity(
            self.identity,
            refresh_token_url="%s%s" % (self.metadata["base_url"], GiteaApiClientPath.oauth_token),
        )

    def get_user(self):
        """Get a user

        See https://gitea.com/api/v1/swagger#/user/userGetCurrent
        """
        return self.get(GiteaApiClientPath.user)

    def search_repos(self):
        """Get repos for a user

        See https://gitea.com/api/v1/swagger#/user/userListRepos
        """
        return self.get(GiteaApiClientPath.user_repos,)

    def get_repo(self, repo):
        """Get repository

        See https://gitea.com/api/v1/swagger#/repository/repoGet
        """
        return self.get(GiteaApiClientPath.repo.format(repo=repo))

    def get_issue(self, repo, issue_index):
        """Get an issue

        See https://gitea.com/api/v1/swagger#/issue/issueGetIssue
        """
        try:
            return self.get(GiteaApiClientPath.issue.format(repo=repo, index=issue_index))
        except IndexError:
            raise ApiError("Issue not found with ID", 404)

    def create_issue(self, repo, data):
        """Create an issue

        See https://gitea.com/api/v1/swagger#/issue/issueCreateIssue
        """
        return self.post(GiteaApiClientPath.issues.format(repo=repo), data=data)

    def create_issue_comment(self, repo, issue_index, data):
        """Create an issue comment

        See https://gitea.com/api/v1/swagger#/issue/issueCreateComment
        """
        return self.post(
            GiteaApiClientPath.comments.format(repo=repo, index=issue_index), data=data
        )

    def search_repo_issues(self, repo, query):
        """Search issues in a repo

        See https://gitea.com/api/v1/swagger#/issue/issueListIssues
        """
        path = GiteaApiClientPath.issues.format(repo=repo)

        return self.get(path, params={"q": query})

    def create_repo_webhook(self, repo):
        """Create a webhook on a repo

        See https://gitea.com/api/v1/swagger#/repository/repoCreateHook
        """
        path = GiteaApiClientPath.repo_hooks.format(repo=repo)
        hook_uri = reverse("sentry-extensions-gitea-webhook")
        model = self.installation.model
        data = {
            "type": "gitea",
            "events": ["push", "pull_request"],
            "active": True,
            "config": {
                "url": absolute_uri(hook_uri),
                "content_type": "json",
                "secret": u"{}:{}".format(model.external_id, model.metadata["webhook_secret"]),
            },
        }
        resp = self.post(path, data)

        return resp["id"]

    def delete_repo_webhook(self, repo, hook_id):
        """Delete a webhook from a project

        See https://gitea.com/api/v1/swagger#/repository/repoDeleteHook
        """
        path = GiteaApiClientPath.repo_hook.format(repo=repo, id=hook_id)
        return self.delete(path)

    def get_last_commits(self, repo):
        """Get the last set of commits ending

        See https://gitea.com/api/v1/swagger#/repository/repoGetAllCommits
        """
        path = GiteaApiClientPath.commits.format(repo=repo)
        return self.get(path)
