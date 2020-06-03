from __future__ import absolute_import

import logging

from .base import BaseEventProcessingStore
from sentry.cache.redis import RedisClusterCache

logger = logging.getLogger(__name__)


class RedisClusterEventProcessingStore(BaseEventProcessingStore):
    def __init__(self, **options):
        super(RedisClusterEventProcessingStore, self).__init__(inner=RedisClusterCache(**options))
