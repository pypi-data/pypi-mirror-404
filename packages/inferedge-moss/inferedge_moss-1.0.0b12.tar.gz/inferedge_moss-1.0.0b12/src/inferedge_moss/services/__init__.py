"""Services package initialization."""

import sys

from .index_service import IndexService

# Skip embedding service in Python 3.14
if sys.version_info < (3, 14):
    from .embedding_service import EmbeddingService

    __all__ = [
        "EmbeddingService",
        "IndexService",
    ]
else:
    __all__ = [
        "IndexService",
    ]
