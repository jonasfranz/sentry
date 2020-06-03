from __future__ import absolute_import

from sentry.cache import default_cache

from .base import BaseEventProcessingStore


class DefaultEventProcessingStore(BaseEventProcessingStore):
    def __init__(self, **options):
        super(DefaultEventProcessingStore, self).__init__(inner=default_cache, **options)
