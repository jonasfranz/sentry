from __future__ import absolute_import
from sentry.utils.cache import cache_key_for_event

DEFAULT_TIMEOUT = 3600


class BaseEventProcessingStore(object):
    def __init__(self, inner, timeout=DEFAULT_TIMEOUT):
        self.inner = inner
        self.timeout = timeout

    def _key_for_event(self, event):
        return cache_key_for_event(event)

    def store(self, event):
        key = self._key_for_event(event)
        self.inner.set(key, event, self.timeout)
        return key

    def get(self, key):
        return self.inner.get(key)

    def delete_by_key(self, key):
        return self.inner.delete(key)

    def delete(self, event):
        return self.inner.delete(self._key_for_event(event))
