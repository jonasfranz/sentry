from __future__ import absolute_import

import re

from django.core.urlresolvers import reverse
from sentry.shared_integrations.exceptions import ApiError, IntegrationError
from sentry.integrations.issues import IssueBasicMixin
from sentry.utils.http import absolute_uri

ISSUE_EXTERNAL_KEY_FORMAT = re.compile(r".+:(.+)/(.+)#(.+)")


class GiteaIssueBasic(IssueBasicMixin):
    def make_external_key(self, data):
        return u"{}:{}".format(self.model.metadata["domain_name"], data["key"])

    def get_issue_url(self, key):
        match = ISSUE_EXTERNAL_KEY_FORMAT.match(key)
        repo, owner, issue_index = match.group(1), match.group(2), match.group(3)
        return u"{}/{}/{}/issues/{}".format(
            self.model.metadata["base_url"], repo, owner, issue_index
        )

    def get_persisted_default_config_fields(self):
        return ["repo"]

    def get_create_issue_config(self, group, **kwargs):
        default_repo, repo_choices = self.get_repository_choices(group, **kwargs)
        kwargs["link_referrer"] = "gitea_integration"
        fields = super(GiteaIssueBasic, self).get_create_issue_config(group, **kwargs)

        org = group.organization
        autocomplete_url = reverse("sentry-extensions-gitea-search", args=[org.slug, self.model.id])

        return [
            {
                "name": "repo",
                "label": "Gitea Repository",
                "type": "select",
                "url": autocomplete_url,
                "choices": repo_choices,
                "defaultValue": default_repo,
                "required": True,
            }
        ] + fields

    def create_issue(self, data, **kwargs):
        client = self.get_client()

        repo = data.get("repo")

        if not repo:
            raise IntegrationError("repo kwarg must be provided")

        try:
            issue = client.create_issue(
                repo=repo, data={"title": data["title"], "body": data["description"]},
            )
        except ApiError as e:
            raise IntegrationError(self.message_from_error(e))

        project_and_issue_index = "%s#%s" % (repo, issue["number"])
        return {
            "key": project_and_issue_index,
            "title": issue["title"],
            "description": issue["body"],
            "url": issue["html_url"],
            "repo": repo,
            "metadata": {"display_name": project_and_issue_index},
        }

    def after_link_issue(self, external_issue, **kwargs):
        data = kwargs["data"]
        repo, issue_index = data.get("externalIssue", "").split("#")
        if not (repo and issue_index):
            raise IntegrationError("Repo and Issue index must be provided")

        client = self.get_client()
        comment = data.get("comment")
        if not comment:
            return

        try:
            client.create_issue_comment(repo=repo, issue_index=issue_index, data={"body": comment})
        except ApiError as e:
            raise IntegrationError(self.message_from_error(e))

    def get_link_issue_config(self, group, **kwargs):
        default_repo, repo_choices = self.get_repository_choices(group, **kwargs)

        org = group.organization
        autocomplete_url = reverse("sentry-extensions-gitea-search", args=[org.slug, self.model.id])

        return [
            {
                "name": "repo",
                "label": "Gitea Repository",
                "type": "select",
                "default": default_repo,
                "choices": repo_choices,
                "url": autocomplete_url,
                "updatesForm": True,
                "required": True,
            },
            {
                "name": "externalIssue",
                "label": "Issue",
                "default": "",
                "type": "select",
                "url": autocomplete_url,
                "required": True,
            },
            {
                "name": "comment",
                "label": "Comment",
                "default": u"Sentry issue: [{issue_id}]({url})".format(
                    url=absolute_uri(
                        group.get_absolute_url(params={"referrer": "gitea_integration"})
                    ),
                    issue_id=group.qualified_short_id,
                ),
                "type": "textarea",
                "required": False,
                "help": ("Leave blank if you don't want to " "add a comment to the Gitea issue."),
            },
        ]

    def get_issue(self, issue_id, **kwargs):
        repo, issue_index = issue_id.split("#")
        client = self.get_client()

        if not repo:
            raise IntegrationError("repo must be provided")

        if not issue_index:
            raise IntegrationError("issue must be provided")

        try:
            issue = client.get_issue(repo, issue_index)
        except ApiError as e:
            raise IntegrationError(self.message_from_error(e))

        project_and_issue_index = "%s#%s" % (repo, issue["number"])
        return {
            "key": project_and_issue_index,
            "title": issue["title"],
            "description": issue["description"],
            "url": issue["html_url"],
            "repo": repo,
            "metadata": {"display_name": project_and_issue_index},
        }

    def get_issue_display_name(self, external_issue):
        return external_issue.metadata["display_name"]
