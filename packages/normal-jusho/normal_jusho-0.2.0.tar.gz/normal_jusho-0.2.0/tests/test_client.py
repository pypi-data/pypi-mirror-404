"""Tests for the Jusho Python SDK.

These tests use httpx's mock transport to avoid real network calls.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, Dict

import httpx
import pytest

from jusho import (
    AsyncJusho,
    Jusho,
    NormalizeResult,
    BatchResult,
    PostalResult,
    SuggestResult,
    ValidationResult,
    ReverseResult,
    NotFoundError,
    RateLimitError,
    ValidationError,
    APIError,
    NetworkError,
    TimeoutError,
    JushoError,
)


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

SAMPLE_NORMALIZE_RESPONSE: Dict[str, Any] = {
    "address": {
        "full": "東京都渋谷区道玄坂一丁目2-3",
        "pref": "東京都",
        "city": "渋谷区",
        "town": "道玄坂一丁目",
        "koaza": "",
        "banchi": "2",
        "go": "3",
        "building": "",
    },
    "address_variants": {
        "kokudo": {"pref": "東京都", "city": "渋谷区", "town": "道玄坂一丁目"},
        "kenall": {"pref": "東京都", "city": "渋谷区", "town": "道玄坂"},
    },
    "kana": {
        "pref": "トウキョウト",
        "city": "シブヤク",
        "town": "ドウゲンザカ",
    },
    "codes": {
        "post_code": "1500043",
        "pref_code": "13",
        "city_code": "13113",
        "town_code": "",
    },
    "geo": {
        "lat": "35.6580",
        "lng": "139.6994",
    },
    "meta": {
        "match_type": "address",
        "is_jigyosyo": False,
        "is_tatemono": False,
        "version": "0.3.6",
    },
}

SAMPLE_BATCH_RESPONSE: Dict[str, Any] = {
    "total": 2,
    "success_count": 1,
    "error_count": 1,
    "results": [
        {
            "input": "東京都渋谷区道玄坂1-2-3",
            "success": True,
            "result": SAMPLE_NORMALIZE_RESPONSE,
            "error": None,
        },
        {
            "input": "存在しない住所",
            "success": False,
            "result": None,
            "error": "住所が見つかりませんでした",
        },
    ],
}

SAMPLE_POSTAL_RESPONSE: Dict[str, Any] = {
    "post_code": "1500043",
    "addresses": [SAMPLE_NORMALIZE_RESPONSE],
}

SAMPLE_SUGGEST_RESPONSE: Dict[str, Any] = {
    "query": "渋谷区道玄",
    "suggestions": [
        {"address": "東京都渋谷区道玄坂一丁目", "post_code": "1500043"},
        {"address": "東京都渋谷区道玄坂二丁目", "post_code": "1500043"},
    ],
}

SAMPLE_VALIDATION_RESPONSE: Dict[str, Any] = {
    "valid": True,
    "normalized": "東京都渋谷区道玄坂一丁目2-3",
    "score": 0.95,
}

SAMPLE_REVERSE_RESPONSE: Dict[str, Any] = {
    "address": {
        "full": "東京都渋谷区道玄坂一丁目",
        "pref": "東京都",
        "city": "渋谷区",
        "town": "道玄坂一丁目",
        "koaza": "",
        "banchi": "",
        "go": "",
        "building": "",
    },
    "codes": {
        "post_code": "1500043",
        "pref_code": "13",
        "city_code": "13113",
        "town_code": "",
    },
    "geo": {
        "lat": "35.6580",
        "lng": "139.6994",
    },
}


def _mock_transport(
    response_data: Any,
    status_code: int = 200,
    headers: Dict[str, str] | None = None,
) -> httpx.MockTransport:
    """Create an httpx MockTransport that returns the given JSON data."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=status_code,
            json=response_data,
            headers=headers or {},
        )

    return httpx.MockTransport(handler)


def _make_sync_client(
    response_data: Any,
    status_code: int = 200,
    headers: Dict[str, str] | None = None,
) -> Jusho:
    """Create a Jusho client backed by a mock transport."""
    transport = _mock_transport(response_data, status_code, headers)
    http_client = httpx.Client(
        transport=transport,
        base_url="https://api.jusho.dev",
    )
    return Jusho(http_client=http_client)


def _make_async_client(
    response_data: Any,
    status_code: int = 200,
    headers: Dict[str, str] | None = None,
) -> AsyncJusho:
    """Create an AsyncJusho client backed by a mock transport."""
    transport = _mock_transport(response_data, status_code, headers)
    http_client = httpx.AsyncClient(
        transport=transport,
        base_url="https://api.jusho.dev",
    )
    return AsyncJusho(http_client=http_client)


# ---------------------------------------------------------------------------
# Normalize tests
# ---------------------------------------------------------------------------

class TestNormalize:
    def test_normalize_success(self) -> None:
        client = _make_sync_client(SAMPLE_NORMALIZE_RESPONSE)
        result = client.normalize("東京都渋谷区道玄坂1-2-3")

        assert isinstance(result, NormalizeResult)
        assert result.address.full == "東京都渋谷区道玄坂一丁目2-3"
        assert result.address.pref == "東京都"
        assert result.address.city == "渋谷区"
        assert result.address.town == "道玄坂一丁目"
        assert result.address.banchi == "2"
        assert result.address.go == "3"

    def test_normalize_codes(self) -> None:
        client = _make_sync_client(SAMPLE_NORMALIZE_RESPONSE)
        result = client.normalize("東京都渋谷区道玄坂1-2-3")

        assert result.codes.post_code == "1500043"
        assert result.codes.pref_code == "13"
        assert result.codes.city_code == "13113"

    def test_normalize_geo(self) -> None:
        client = _make_sync_client(SAMPLE_NORMALIZE_RESPONSE)
        result = client.normalize("東京都渋谷区道玄坂1-2-3")

        assert result.geo.lat == "35.6580"
        assert result.geo.lng == "139.6994"

    def test_normalize_kana(self) -> None:
        client = _make_sync_client(SAMPLE_NORMALIZE_RESPONSE)
        result = client.normalize("東京都渋谷区道玄坂1-2-3")

        assert result.kana.pref == "トウキョウト"
        assert result.kana.city == "シブヤク"

    def test_normalize_meta(self) -> None:
        client = _make_sync_client(SAMPLE_NORMALIZE_RESPONSE)
        result = client.normalize("東京都渋谷区道玄坂1-2-3")

        assert result.meta.match_type == "address"
        assert result.meta.is_jigyosyo is False
        assert result.meta.is_tatemono is False

    def test_normalize_address_variants(self) -> None:
        client = _make_sync_client(SAMPLE_NORMALIZE_RESPONSE)
        result = client.normalize("東京都渋谷区道玄坂1-2-3")

        assert result.address_variants.kokudo.town == "道玄坂一丁目"
        assert result.address_variants.kenall.town == "道玄坂"

    def test_normalize_raw_preserved(self) -> None:
        client = _make_sync_client(SAMPLE_NORMALIZE_RESPONSE)
        result = client.normalize("東京都渋谷区道玄坂1-2-3")

        assert result.raw == SAMPLE_NORMALIZE_RESPONSE

    def test_normalize_not_found(self) -> None:
        client = _make_sync_client(
            {"detail": "住所が見つかりませんでした"},
            status_code=404,
        )
        with pytest.raises(NotFoundError) as exc_info:
            client.normalize("存在しない住所")
        assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# Batch tests
# ---------------------------------------------------------------------------

class TestBatch:
    def test_batch_success(self) -> None:
        client = _make_sync_client(SAMPLE_BATCH_RESPONSE)
        result = client.normalize_batch(["東京都渋谷区道玄坂1-2-3", "存在しない住所"])

        assert isinstance(result, BatchResult)
        assert result.total == 2
        assert result.success_count == 1
        assert result.error_count == 1
        assert len(result.results) == 2

    def test_batch_items(self) -> None:
        client = _make_sync_client(SAMPLE_BATCH_RESPONSE)
        result = client.normalize_batch(["東京都渋谷区道玄坂1-2-3", "存在しない住所"])

        # First item: success
        item0 = result.results[0]
        assert item0.success is True
        assert item0.result is not None
        assert item0.result.address.pref == "東京都"
        assert item0.error is None

        # Second item: failure
        item1 = result.results[1]
        assert item1.success is False
        assert item1.result is None
        assert item1.error == "住所が見つかりませんでした"


# ---------------------------------------------------------------------------
# Postal tests
# ---------------------------------------------------------------------------

class TestPostal:
    def test_postal_success(self) -> None:
        client = _make_sync_client(SAMPLE_POSTAL_RESPONSE)
        result = client.postal("1500043")

        assert isinstance(result, PostalResult)
        assert result.post_code == "1500043"
        assert len(result.addresses) == 1
        assert result.addresses[0].address.pref == "東京都"


# ---------------------------------------------------------------------------
# Suggest tests
# ---------------------------------------------------------------------------

class TestSuggest:
    def test_suggest_success(self) -> None:
        client = _make_sync_client(SAMPLE_SUGGEST_RESPONSE)
        result = client.suggest("渋谷区道玄")

        assert isinstance(result, SuggestResult)
        assert result.query == "渋谷区道玄"
        assert len(result.suggestions) == 2
        assert result.suggestions[0].address == "東京都渋谷区道玄坂一丁目"
        assert result.suggestions[0].post_code == "1500043"


# ---------------------------------------------------------------------------
# Validate tests
# ---------------------------------------------------------------------------

class TestValidate:
    def test_validate_success(self) -> None:
        client = _make_sync_client(SAMPLE_VALIDATION_RESPONSE)
        result = client.validate("東京都渋谷区道玄坂1-2-3")

        assert isinstance(result, ValidationResult)
        assert result.valid is True
        assert result.normalized == "東京都渋谷区道玄坂一丁目2-3"
        assert result.score == 0.95


# ---------------------------------------------------------------------------
# Reverse tests
# ---------------------------------------------------------------------------

class TestReverse:
    def test_reverse_success(self) -> None:
        client = _make_sync_client(SAMPLE_REVERSE_RESPONSE)
        result = client.reverse("東京都渋谷区道玄坂1-2-3")

        assert isinstance(result, ReverseResult)
        assert result.address.pref == "東京都"
        assert result.codes.post_code == "1500043"
        assert result.geo.lat == "35.6580"


# ---------------------------------------------------------------------------
# Error handling tests
# ---------------------------------------------------------------------------

class TestErrors:
    def test_rate_limit_error(self) -> None:
        client = _make_sync_client(
            {"detail": "Rate limit exceeded"},
            status_code=429,
            headers={"Retry-After": "60"},
        )
        with pytest.raises(RateLimitError) as exc_info:
            client.normalize("東京都渋谷区道玄坂1-2-3")
        assert exc_info.value.status_code == 429
        assert exc_info.value.retry_after == 60

    def test_validation_error(self) -> None:
        client = _make_sync_client(
            {"detail": "address is required"},
            status_code=422,
        )
        with pytest.raises(ValidationError) as exc_info:
            client.normalize("")
        assert exc_info.value.status_code == 422

    def test_api_error(self) -> None:
        client = _make_sync_client(
            {"error": "Internal server error"},
            status_code=500,
        )
        with pytest.raises(APIError) as exc_info:
            client.normalize("東京都渋谷区道玄坂1-2-3")
        assert exc_info.value.status_code == 500

    def test_error_hierarchy(self) -> None:
        """All errors inherit from JushoError."""
        assert issubclass(NotFoundError, JushoError)
        assert issubclass(RateLimitError, JushoError)
        assert issubclass(ValidationError, JushoError)
        assert issubclass(APIError, JushoError)
        assert issubclass(NetworkError, JushoError)
        assert issubclass(TimeoutError, JushoError)


# ---------------------------------------------------------------------------
# Client lifecycle tests
# ---------------------------------------------------------------------------

class TestClientLifecycle:
    def test_context_manager(self) -> None:
        transport = _mock_transport(SAMPLE_NORMALIZE_RESPONSE)
        http_client = httpx.Client(
            transport=transport,
            base_url="https://api.jusho.dev",
        )
        with Jusho(http_client=http_client) as client:
            result = client.normalize("東京都渋谷区道玄坂1-2-3")
            assert result.address.pref == "東京都"

    def test_default_construction(self) -> None:
        """Ensure Jusho() can be constructed with defaults."""
        client = Jusho()
        assert client is not None
        client.close()

    def test_custom_base_url_and_timeout(self) -> None:
        client = Jusho(base_url="https://custom.example.com", timeout=30.0)
        assert client is not None
        client.close()


# ---------------------------------------------------------------------------
# Async client tests
# ---------------------------------------------------------------------------

class TestAsyncClient:
    def test_async_normalize(self) -> None:
        client = _make_async_client(SAMPLE_NORMALIZE_RESPONSE)

        async def run() -> NormalizeResult:
            async with client:
                return await client.normalize("東京都渋谷区道玄坂1-2-3")

        result = asyncio.run(run())
        assert isinstance(result, NormalizeResult)
        assert result.address.pref == "東京都"
        assert result.codes.post_code == "1500043"

    def test_async_batch(self) -> None:
        client = _make_async_client(SAMPLE_BATCH_RESPONSE)

        async def run() -> BatchResult:
            async with client:
                return await client.normalize_batch(["addr1", "addr2"])

        result = asyncio.run(run())
        assert isinstance(result, BatchResult)
        assert result.total == 2

    def test_async_not_found(self) -> None:
        client = _make_async_client(
            {"detail": "Not found"},
            status_code=404,
        )

        async def run() -> None:
            async with client:
                await client.normalize("nope")

        with pytest.raises(NotFoundError):
            asyncio.run(run())


# ---------------------------------------------------------------------------
# Model edge cases
# ---------------------------------------------------------------------------

class TestModelEdgeCases:
    def test_empty_response_fields(self) -> None:
        """Ensure missing fields default gracefully."""
        client = _make_sync_client({})
        result = client.normalize("test")

        assert result.address.full == ""
        assert result.address.pref == ""
        assert result.codes.post_code == ""
        assert result.geo.lat == ""
        assert result.meta.match_type == ""
        assert result.building_info is None
        assert result.jigyosyo_info is None

    def test_building_info_present(self) -> None:
        data = {
            **SAMPLE_NORMALIZE_RESPONSE,
            "building_info": {
                "building": "六本木ヒルズ森タワー",
                "building_short": "森タワー",
                "floor": "30",
                "floor_kanji": "三十階",
                "room": "",
            },
        }
        client = _make_sync_client(data)
        result = client.normalize("test")

        assert result.building_info is not None
        assert result.building_info.building == "六本木ヒルズ森タワー"
        assert result.building_info.floor == "30"
        assert result.building_info.floor_kanji == "三十階"

    def test_jigyosyo_info_present(self) -> None:
        data = {
            **SAMPLE_NORMALIZE_RESPONSE,
            "jigyosyo_info": {
                "jigyosyo_name": "宮内庁",
                "jigyosyo_name_kana": "クナイチョウ",
                "handling_office": "千代田",
                "address_detail": "1-1",
            },
        }
        client = _make_sync_client(data)
        result = client.normalize("test")

        assert result.jigyosyo_info is not None
        assert result.jigyosyo_info.jigyosyo_name == "宮内庁"
        assert result.jigyosyo_info.handling_office == "千代田"
