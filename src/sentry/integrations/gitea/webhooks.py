from __future__ import absolute_import

import dateutil.parser
import logging
import six
import hmac
import hashlib

from django.db import IntegrityError, transaction
from django.http import HttpResponse, Http404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from django.utils import timezone
from django.utils.crypto import constant_time_compare
from simplejson import JSONDecodeError

from sentry.models import Commit, CommitAuthor, Integration, PullRequest, Repository
from sentry.plugins.providers import IntegrationRepositoryProvider
from sentry.utils import json

logger = logging.getLogger("sentry.webhooks")

PROVIDER_NAME = "integrations:gitea"


class Webhook(object):
    def __call__(self, integration, organization, event):
        raise NotImplementedError

    def get_repo(self, integration, organization, event):
        """
        Given a webhook payload, get the associated Repository record.

        Assumes repo in event payload.
        """
        try:
            repo_name = event["repository"]["full_name"]
        except KeyError:
            logger.info("gitea.webhook.missing-repo-name", extra={"integration_id": integration.id})
            raise Http404()

        external_id = u"{}:{}".format(integration.metadata["instance"], repo_name)
        try:
            repo = Repository.objects.get(
                organization_id=organization.id, provider=PROVIDER_NAME, external_id=external_id
            )
        except Repository.DoesNotExist:
            return None
        return repo

    def update_repo_data(self, repo, event):
        """
        Given a webhook payload, update stored repo data if needed.

        Assumes a "repository" key in event payload, with certain subkeys.
        """

        event_repo = event["repository"]

        repo_name_from_event = event_repo["full_name"]
        url_from_event = event_repo["html_url"]

        if (
            repo.name != repo_name_from_event
            or repo.url != url_from_event
            or repo.config.get("repo") != repo_name_from_event
        ):
            repo.update(
                name=repo_name_from_event,
                url=url_from_event,
                config=dict(repo.config, path=repo_name_from_event),
            )


class PullRequestEventWebhook(Webhook):
    """
    Handle Pull Request Hook
    """

    def __call__(self, integration, organization, event):
        repo = self.get_repo(integration, organization, event)
        if repo is None:
            return
        self.update_repo_data(repo, event)

        author_email = None
        try:
            pull_request = event["pull_request"]

            number = pull_request["number"]
            title = pull_request["title"]
            body = pull_request["body"]
            created_at = pull_request["created_at"]
            author_name = pull_request["user"]["username"]
            author_email = pull_request["user"]["email"]
            merge_commit_sha = pull_request["merge_commit_sha"] if pull_request["merged"] else None
        except KeyError as e:
            logger.info(
                "gitea.webhook.invalid-pull-request-data",
                extra={"integration_id": integration.id, "error": six.text_type(e)},
            )

        if not author_email:
            raise Http404()

        author = CommitAuthor.objects.get_or_create(
            organization_id=organization.id, email=author_email, defaults={"name": author_name}
        )[0]

        try:
            PullRequest.create_or_save(
                organization_id=organization.id,
                repository_id=repo.id,
                key=number,
                values={
                    "title": title,
                    "author": author,
                    "message": body,
                    "merge_commit_sha": merge_commit_sha,
                    "date_added": dateutil.parser.parse(created_at).astimezone(timezone.utc),
                },
            )
        except IntegrityError:
            pass


class PushEventWebhook(Webhook):
    """
    Handle push hook
    """

    def __call__(self, integration, organization, event):
        repo = self.get_repo(integration, organization, event)
        if repo is None:
            return

        self.update_repo_data(repo, event)

        authors = {}

        for commit in event.get("commits", []):
            if IntegrationRepositoryProvider.should_ignore_commit(commit["message"]):
                continue

            author_email = commit["author"]["email"]

            # TODO: we need to deal with bad values here, but since
            # its optional, lets just throw it out for now
            if author_email is None or len(author_email) > 75:
                author = None
            elif author_email not in authors:
                authors[author_email] = author = CommitAuthor.objects.get_or_create(
                    organization_id=organization.id,
                    email=author_email,
                    defaults={"name": commit["author"]["name"]},
                )[0]
            else:
                author = authors[author_email]
            try:
                with transaction.atomic():
                    Commit.objects.create(
                        repository_id=repo.id,
                        organization_id=organization.id,
                        key=commit["id"],
                        message=commit["message"],
                        author=author,
                        date_added=dateutil.parser.parse(commit["timestamp"]).astimezone(
                            timezone.utc
                        ),
                    )
            except IntegrityError:
                pass


class GiteaWebhookEndpoint(View):
    provider = "gitea"

    _handlers = {"push": PushEventWebhook, "pull_request": PullRequestEventWebhook}

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        if request.method != "POST":
            return HttpResponse(status=405)

        return super(GiteaWebhookEndpoint, self).dispatch(request, *args, **kwargs)

    def check_signature(self, body, secret, signature):
        # See https://docs.gitea.io/en-us/webhooks/
        mod = hashlib.sha256
        expected = hmac.new(key=secret.encode("utf-8"), msg=body, digestmod=mod).hexdigest()
        return constant_time_compare(expected, signature)

    def post(self, request):
        signature = "<unknown>"
        try:
            signature = request.META["HTTP_X_GITEA_SIGNATURE"]
        except Exception:
            logger.info("gitea.webhook.no-signature", extra={"signature": signature})
            return HttpResponse(status=400)

        try:
            event = json.loads(request.body.decode("utf-8"))
        except JSONDecodeError:
            logger.info("gitea.webhook.invalid-json")
            return HttpResponse(status=400)

        external_id = None
        webhook_secret = None
        try:
            external_id, webhook_secret = event["secret"].split("#")
        except Exception:
            logger.info("gitea.webhook.invalid-secret", extra={"externalId": external_id})
            return HttpResponse(status=400)

        if not self.check_signature(six.binary_type(request.body), event["secret"], signature):
            logger.info(
                "gitea.webhook.invalid-signature",
                extra={"secret": event["secret"], "signature": signature},
            )
            return HttpResponse(status=400)

        try:
            integration = (
                Integration.objects.filter(provider=self.provider, external_id=external_id)
                .prefetch_related("organizations")
                .get()
            )
        except Integration.DoesNotExist:
            logger.info(
                "gitea.webhook.invalid-organization", extra={"external_id": external_id},
            )
            return HttpResponse(status=400)

        if not constant_time_compare(webhook_secret, integration.metadata["webhook_secret"]):
            logger.info(
                "gitea.webhook.invalid-token-secret", extra={"integration_id": integration.id}
            )
            return HttpResponse(status=400)

        try:
            handler = self._handlers[request.META["HTTP_X_GITEA_EVENT"]]
        except KeyError:
            logger.info(
                "gitea.webhook.missing-event", extra={"event": request.META["HTTP_X_GITEA_EVENT"]}
            )
            return HttpResponse(status=400)

        for organization in integration.organizations.all():
            handler()(integration, organization, event)
        return HttpResponse(status=204)
