"""Jusho -- Python SDK for Japanese address normalization.

Quick start::

    from jusho import Jusho

    client = Jusho()
    result = client.normalize("東京都渋谷区道玄坂1-2-3")
    print(result.address.full)
    print(result.codes.post_code)

Async usage::

    from jusho import AsyncJusho

    async with AsyncJusho() as client:
        result = await client.normalize("東京都渋谷区道玄坂1-2-3")
"""

from __future__ import annotations

from .async_client import AsyncJusho
from .client import Jusho
from .errors import (
    APIError,
    JushoError,
    NetworkError,
    NotFoundError,
    RateLimitError,
    TimeoutError,
    ValidationError,
)
from .models import (
    AddressInfo,
    AddressVariantsInfo,
    BatchResult,
    BatchResultItem,
    BuildingInfo,
    CodesInfo,
    GeoInfo,
    JigyosyoInfo,
    KanaInfo,
    MetaInfo,
    NormalizeResult,
    PostalResult,
    ReverseResult,
    RomajiInfo,
    SuggestItem,
    SuggestResult,
    ToorinaInfo,
    ValidationResult,
    VariantAddress,
)

__version__ = "0.2.0"

__all__ = [
    # Clients
    "Jusho",
    "AsyncJusho",
    # Response models
    "AddressInfo",
    "AddressVariantsInfo",
    "BatchResult",
    "BatchResultItem",
    "BuildingInfo",
    "CodesInfo",
    "GeoInfo",
    "JigyosyoInfo",
    "KanaInfo",
    "MetaInfo",
    "NormalizeResult",
    "PostalResult",
    "ReverseResult",
    "RomajiInfo",
    "SuggestItem",
    "SuggestResult",
    "ToorinaInfo",
    "ValidationResult",
    "VariantAddress",
    # Errors
    "APIError",
    "JushoError",
    "NetworkError",
    "NotFoundError",
    "RateLimitError",
    "TimeoutError",
    "ValidationError",
    # Meta
    "__version__",
]
