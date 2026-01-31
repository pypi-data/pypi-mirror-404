"""Response models for the Jusho API.

All models are pure dataclasses with no external dependencies.
They mirror the JSON structure returned by the Jusho API endpoints.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Normalize response models
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AddressInfo:
    """Structured address components.

    Attributes:
        full: The fully normalized address string.
        pref: Prefecture (e.g. ``"東京都"``).
        city: City / ward / town / village (e.g. ``"渋谷区"``).
        town: Town area including chome (e.g. ``"道玄坂一丁目"``).
        koaza: Sub-area (koaza).
        banchi: Block number (banchi).
        go: Building / lot number (go).
        building: Building name, floor, room info.
    """

    full: str = ""
    pref: str = ""
    city: str = ""
    town: str = ""
    koaza: str = ""
    banchi: str = ""
    go: str = ""
    building: str = ""


@dataclass(frozen=True)
class VariantAddress:
    """Address representation from a specific data source.

    Attributes:
        pref: Prefecture.
        city: City.
        town: Town area.
    """

    pref: str = ""
    city: str = ""
    town: str = ""


@dataclass(frozen=True)
class AddressVariantsInfo:
    """Address variants by data source.

    The same physical address may be written differently depending on
    the data source.  For example, ``袖ケ浦市`` (kenall / Japan Post) vs
    ``袖ヶ浦市`` (kokudo / MLIT).

    Attributes:
        kokudo: MLIT (Ministry of Land) representation.
        kenall: Japan Post (KEN ALL) representation.
    """

    kokudo: VariantAddress = field(default_factory=VariantAddress)
    kenall: VariantAddress = field(default_factory=VariantAddress)


@dataclass(frozen=True)
class KanaInfo:
    """Katakana readings for address components.

    Attributes:
        pref: Prefecture reading in katakana.
        city: City reading in katakana.
        town: Town reading in katakana.
    """

    pref: str = ""
    city: str = ""
    town: str = ""


@dataclass(frozen=True)
class CodesInfo:
    """Administrative and postal codes.

    Attributes:
        post_code: 7-digit postal code (e.g. ``"1500043"``).
        pref_code: JIS prefecture code (e.g. ``"13"``).
        city_code: JIS municipality code (e.g. ``"13113"``).
        town_code: Town area code.
    """

    post_code: str = ""
    pref_code: str = ""
    city_code: str = ""
    town_code: str = ""


@dataclass(frozen=True)
class GeoInfo:
    """Geographic coordinates.

    Attributes:
        lat: Latitude as a string.
        lng: Longitude as a string.
    """

    lat: str = ""
    lng: str = ""


@dataclass(frozen=True)
class MetaInfo:
    """Metadata about the normalization result.

    Attributes:
        match_type: How the address was matched
            (``"address"``, ``"building"``, or ``"jigyosyo"``).
        match_level: Match level (0=none, 1=pref, 2=city, 3=town, 4=block, 5=full).
        match_level_label: Match level label ("none", "pref", "city", "town", "block", "full").
        confidence: Confidence score (0.0-1.0).
        is_jigyosyo: True if matched via the business-office dictionary.
        is_tatemono: True if matched via the large-building dictionary.
        version: API version string.
    """

    match_type: str = ""
    match_level: int = 0
    match_level_label: str = ""
    confidence: float = 0.0
    is_jigyosyo: bool = False
    is_tatemono: bool = False
    version: str = ""


@dataclass(frozen=True)
class RomajiInfo:
    """Romaji (romanized) readings for address components.

    Attributes:
        pref: Prefecture in romaji.
        city: City in romaji.
        town: Town in romaji.
        full: Full address in romaji.
    """

    pref: str = ""
    city: str = ""
    town: str = ""
    full: str = ""


@dataclass(frozen=True)
class ToorinaInfo:
    """Kyoto street name (通り名) information.

    Only present for Kyoto city addresses that include street directions.

    Attributes:
        value: Street name value (e.g., "烏丸通御池上ル").
        full_address_with_toorina: Full address including street name.
    """

    value: str = ""
    full_address_with_toorina: str = ""


@dataclass(frozen=True)
class BuildingInfo:
    """Extra information when the match is a large building.

    Attributes:
        building: Full building name.
        building_short: Abbreviated building name.
        floor: Floor number (Arabic numeral string).
        floor_kanji: Floor in kanji (e.g. ``"三十階"``).
        room: Room number.
    """

    building: str = ""
    building_short: str = ""
    floor: str = ""
    floor_kanji: str = ""
    room: str = ""


@dataclass(frozen=True)
class JigyosyoInfo:
    """Extra information when the match is a business office.

    Attributes:
        jigyosyo_name: Business office name.
        jigyosyo_name_kana: Business office name in katakana.
        handling_office: Post office that handles this office's mail.
        address_detail: Detailed address (block / lot).
    """

    jigyosyo_name: str = ""
    jigyosyo_name_kana: str = ""
    handling_office: str = ""
    address_detail: str = ""


@dataclass(frozen=True)
class NormalizeResult:
    """Result of a single address normalization.

    This is the primary model returned by :pymeth:`Jusho.normalize` and
    :pymeth:`AsyncJusho.normalize`.

    Attributes:
        address: Structured address components.
        address_variants: Data-source-specific address representations.
        kana: Katakana readings.
        romaji: Romaji (romanized) readings.
        codes: Postal and administrative codes.
        geo: Geographic coordinates.
        meta: Match metadata.
        toorina: Kyoto street name info (通り名) - only present for Kyoto addresses.
        building_info: Present only when ``meta.is_tatemono`` is True.
        jigyosyo_info: Present only when ``meta.is_jigyosyo`` is True.
        raw: The raw JSON dict returned by the API.
    """

    address: AddressInfo = field(default_factory=AddressInfo)
    address_variants: AddressVariantsInfo = field(default_factory=AddressVariantsInfo)
    kana: KanaInfo = field(default_factory=KanaInfo)
    romaji: Optional[RomajiInfo] = None
    codes: CodesInfo = field(default_factory=CodesInfo)
    geo: GeoInfo = field(default_factory=GeoInfo)
    meta: MetaInfo = field(default_factory=MetaInfo)
    toorina: Optional[ToorinaInfo] = None
    building_info: Optional[BuildingInfo] = None
    jigyosyo_info: Optional[JigyosyoInfo] = None
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)


# ---------------------------------------------------------------------------
# Batch response models
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BatchResultItem:
    """A single item inside a batch normalization response.

    Attributes:
        input: The original input address string.
        success: Whether normalization succeeded.
        result: The normalization result (present when ``success`` is True).
        error: Error message (present when ``success`` is False).
    """

    input: str = ""
    success: bool = False
    result: Optional[NormalizeResult] = None
    error: Optional[str] = None


@dataclass(frozen=True)
class BatchResult:
    """Result of a batch address normalization.

    Attributes:
        total: Number of input addresses.
        success_count: Number that were successfully normalized.
        error_count: Number that failed normalization.
        results: Per-address results.
        raw: The raw JSON dict returned by the API.
    """

    total: int = 0
    success_count: int = 0
    error_count: int = 0
    results: List[BatchResultItem] = field(default_factory=list)
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)


# ---------------------------------------------------------------------------
# Postal lookup response
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PostalResult:
    """Result of a postal code lookup.

    Attributes:
        post_code: The queried postal code.
        addresses: List of address matches for this postal code.
        raw: The raw JSON dict returned by the API.
    """

    post_code: str = ""
    addresses: List[NormalizeResult] = field(default_factory=list)
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)


# ---------------------------------------------------------------------------
# Suggest response
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SuggestItem:
    """A single suggestion entry.

    Attributes:
        address: Suggested full address string.
        post_code: Postal code if available.
    """

    address: str = ""
    post_code: str = ""


@dataclass(frozen=True)
class SuggestResult:
    """Result of an address suggestion / autocomplete query.

    Attributes:
        query: The original query string.
        suggestions: List of suggestion items.
        raw: The raw JSON dict returned by the API.
    """

    query: str = ""
    suggestions: List[SuggestItem] = field(default_factory=list)
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)


# ---------------------------------------------------------------------------
# Validate response
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ValidationResult:
    """Result of an address validation check.

    Attributes:
        valid: Whether the address is recognized as valid.
        normalized: The normalized form of the address (if valid).
        score: Confidence score (0.0 -- 1.0) if provided by the API.
        raw: The raw JSON dict returned by the API.
    """

    valid: bool = False
    normalized: Optional[str] = None
    score: Optional[float] = None
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)


# ---------------------------------------------------------------------------
# Reverse response
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ReverseResult:
    """Result of a reverse address lookup.

    Attributes:
        address: Resolved address information.
        codes: Postal and administrative codes.
        geo: Geographic coordinates.
        raw: The raw JSON dict returned by the API.
    """

    address: AddressInfo = field(default_factory=AddressInfo)
    codes: CodesInfo = field(default_factory=CodesInfo)
    geo: GeoInfo = field(default_factory=GeoInfo)
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)


# ---------------------------------------------------------------------------
# Parsing helpers (internal)
# ---------------------------------------------------------------------------

def _parse_address_info(data: Dict[str, Any]) -> AddressInfo:
    """Parse an ``address`` sub-object from JSON."""
    return AddressInfo(
        full=data.get("full", ""),
        pref=data.get("pref", ""),
        city=data.get("city", ""),
        town=data.get("town", ""),
        koaza=data.get("koaza", ""),
        banchi=data.get("banchi", ""),
        go=data.get("go", ""),
        building=data.get("building", ""),
    )


def _parse_variant_address(data: Dict[str, Any]) -> VariantAddress:
    return VariantAddress(
        pref=data.get("pref", ""),
        city=data.get("city", ""),
        town=data.get("town", ""),
    )


def _parse_address_variants(data: Dict[str, Any]) -> AddressVariantsInfo:
    return AddressVariantsInfo(
        kokudo=_parse_variant_address(data.get("kokudo", {})),
        kenall=_parse_variant_address(data.get("kenall", {})),
    )


def _parse_kana(data: Dict[str, Any]) -> KanaInfo:
    return KanaInfo(
        pref=data.get("pref", ""),
        city=data.get("city", ""),
        town=data.get("town", ""),
    )


def _parse_codes(data: Dict[str, Any]) -> CodesInfo:
    return CodesInfo(
        post_code=data.get("post_code", ""),
        pref_code=data.get("pref_code", ""),
        city_code=data.get("city_code", ""),
        town_code=data.get("town_code", ""),
    )


def _parse_geo(data: Dict[str, Any]) -> GeoInfo:
    return GeoInfo(
        lat=data.get("lat", ""),
        lng=data.get("lng", ""),
    )


def _parse_meta(data: Dict[str, Any]) -> MetaInfo:
    return MetaInfo(
        match_type=data.get("match_type", ""),
        match_level=data.get("match_level", 0),
        match_level_label=data.get("match_level_label", ""),
        confidence=data.get("confidence", 0.0),
        is_jigyosyo=data.get("is_jigyosyo", False),
        is_tatemono=data.get("is_tatemono", False),
        version=data.get("version", ""),
    )


def _parse_romaji(data: Optional[Dict[str, Any]]) -> Optional[RomajiInfo]:
    if data is None:
        return None
    return RomajiInfo(
        pref=data.get("pref", ""),
        city=data.get("city", ""),
        town=data.get("town", ""),
        full=data.get("full", ""),
    )


def _parse_toorina(data: Optional[Dict[str, Any]]) -> Optional[ToorinaInfo]:
    if data is None:
        return None
    return ToorinaInfo(
        value=data.get("value", ""),
        full_address_with_toorina=data.get("full_address_with_toorina", ""),
    )


def _parse_building_info(data: Optional[Dict[str, Any]]) -> Optional[BuildingInfo]:
    if data is None:
        return None
    return BuildingInfo(
        building=data.get("building", ""),
        building_short=data.get("building_short", ""),
        floor=data.get("floor", ""),
        floor_kanji=data.get("floor_kanji", ""),
        room=data.get("room", ""),
    )


def _parse_jigyosyo_info(data: Optional[Dict[str, Any]]) -> Optional[JigyosyoInfo]:
    if data is None:
        return None
    return JigyosyoInfo(
        jigyosyo_name=data.get("jigyosyo_name", ""),
        jigyosyo_name_kana=data.get("jigyosyo_name_kana", ""),
        handling_office=data.get("handling_office", ""),
        address_detail=data.get("address_detail", ""),
    )


def _parse_normalize_result(data: Dict[str, Any]) -> NormalizeResult:
    """Parse a full normalize response dict into a ``NormalizeResult``."""
    return NormalizeResult(
        address=_parse_address_info(data.get("address", {})),
        address_variants=_parse_address_variants(data.get("address_variants", {})),
        kana=_parse_kana(data.get("kana", {})),
        romaji=_parse_romaji(data.get("romaji")),
        codes=_parse_codes(data.get("codes", {})),
        geo=_parse_geo(data.get("geo", {})),
        meta=_parse_meta(data.get("meta", {})),
        toorina=_parse_toorina(data.get("toorina")),
        building_info=_parse_building_info(data.get("building_info")),
        jigyosyo_info=_parse_jigyosyo_info(data.get("jigyosyo_info")),
        raw=data,
    )


def _parse_batch_result_item(data: Dict[str, Any]) -> BatchResultItem:
    result_data = data.get("result")
    parsed_result = _parse_normalize_result(result_data) if result_data else None
    return BatchResultItem(
        input=data.get("input", ""),
        success=data.get("success", False),
        result=parsed_result,
        error=data.get("error"),
    )


def _parse_batch_result(data: Dict[str, Any]) -> BatchResult:
    """Parse a batch normalize response dict into a ``BatchResult``."""
    items = [_parse_batch_result_item(item) for item in data.get("results", [])]
    return BatchResult(
        total=data.get("total", 0),
        success_count=data.get("success_count", 0),
        error_count=data.get("error_count", 0),
        results=items,
        raw=data,
    )


def _parse_postal_result(data: Dict[str, Any]) -> PostalResult:
    """Parse a postal lookup response."""
    addresses_raw = data.get("addresses", [])
    addresses = [_parse_normalize_result(a) for a in addresses_raw]
    return PostalResult(
        post_code=data.get("post_code", ""),
        addresses=addresses,
        raw=data,
    )


def _parse_suggest_result(data: Dict[str, Any]) -> SuggestResult:
    """Parse a suggest response."""
    items = [
        SuggestItem(
            address=s.get("address", ""),
            post_code=s.get("post_code", ""),
        )
        for s in data.get("suggestions", [])
    ]
    return SuggestResult(
        query=data.get("query", ""),
        suggestions=items,
        raw=data,
    )


def _parse_validation_result(data: Dict[str, Any]) -> ValidationResult:
    """Parse a validation response."""
    return ValidationResult(
        valid=data.get("valid", False),
        normalized=data.get("normalized"),
        score=data.get("score"),
        raw=data,
    )


def _parse_reverse_result(data: Dict[str, Any]) -> ReverseResult:
    """Parse a reverse lookup response."""
    return ReverseResult(
        address=_parse_address_info(data.get("address", {})),
        codes=_parse_codes(data.get("codes", {})),
        geo=_parse_geo(data.get("geo", {})),
        raw=data,
    )
