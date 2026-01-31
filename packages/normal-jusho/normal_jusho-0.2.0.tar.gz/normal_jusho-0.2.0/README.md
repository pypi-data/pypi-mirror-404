# Jusho Python SDK

Python client for the [Jusho](https://jusho.dev) Japanese address normalization API.

Jusho normalizes free-form Japanese address strings into structured, machine-readable data including postal codes, prefecture/city/town breakdown, katakana readings, administrative codes, and geographic coordinates.

## Installation

```bash
pip install normal-jusho
```

## Quick Start

```python
from jusho import Jusho

client = Jusho()

result = client.normalize("東京都渋谷区道玄坂1-2-3")

print(result.address.full)       # "東京都渋谷区道玄坂一丁目2-3"
print(result.address.pref)       # "東京都"
print(result.address.city)       # "渋谷区"
print(result.codes.post_code)    # "1500043"
print(result.geo.lat)            # "35.6580"
print(result.kana.pref)          # "トウキョウト"
print(result.meta.match_type)    # "address"
```

## Features

- **Sync and async** clients (`Jusho` and `AsyncJusho`)
- **Typed responses** with full type-hint support (PEP 561)
- **Structured error handling** with a clear exception hierarchy
- **Zero required dependencies** beyond `httpx`
- **Python 3.9+** support

## API Reference

### Client Initialization

```python
from jusho import Jusho

# Default settings
client = Jusho()

# Custom configuration
client = Jusho(
    base_url="https://api.jusho.dev",
    timeout=15.0,
    headers={"Authorization": "Bearer YOUR_TOKEN"},
)

# Use as context manager
with Jusho() as client:
    result = client.normalize("...")
```

### Normalize

Normalize a single Japanese address:

```python
result = client.normalize("東京都千代田区千代田1-1")

# Address components
result.address.full       # Full normalized address
result.address.pref       # Prefecture
result.address.city       # City / ward
result.address.town       # Town area (with chome)
result.address.koaza      # Sub-area
result.address.banchi     # Block number
result.address.go         # Lot number
result.address.building   # Building name

# Data source variants
result.address_variants.kokudo.pref   # MLIT representation
result.address_variants.kenall.pref   # Japan Post representation

# Codes
result.codes.post_code    # Postal code (7 digits)
result.codes.pref_code    # Prefecture code
result.codes.city_code    # Municipality code

# Geography
result.geo.lat            # Latitude
result.geo.lng            # Longitude

# Katakana
result.kana.pref          # Prefecture reading
result.kana.city          # City reading
result.kana.town          # Town reading

# Metadata
result.meta.match_type    # "address", "building", or "jigyosyo"
result.meta.is_jigyosyo   # Business office match
result.meta.is_tatemono   # Large building match
```

### Batch Normalize

Normalize up to 100 addresses in a single request:

```python
result = client.normalize_batch([
    "東京都千代田区千代田1-1",
    "大阪府大阪市北区梅田1-1-1",
])

print(result.total)          # 2
print(result.success_count)  # Number of successful normalizations

for item in result.results:
    if item.success:
        print(item.result.address.full)
    else:
        print(f"Error: {item.error}")
```

### Postal Code Lookup

```python
result = client.postal("1500043")

print(result.post_code)
for addr in result.addresses:
    print(addr.address.full)
```

### Address Suggestions

```python
result = client.suggest("渋谷区道玄")

for suggestion in result.suggestions:
    print(suggestion.address, suggestion.post_code)
```

### Validation

```python
result = client.validate("東京都渋谷区道玄坂1-2-3")

print(result.valid)       # True / False
print(result.normalized)  # Normalized form
print(result.score)       # Confidence score
```

### Reverse Lookup

```python
result = client.reverse("東京都渋谷区道玄坂1-2-3")

print(result.address.pref)
print(result.codes.post_code)
```

## Async Usage

```python
import asyncio
from jusho import AsyncJusho

async def main():
    async with AsyncJusho() as client:
        result = await client.normalize("東京都渋谷区道玄坂1-2-3")
        print(result.address.full)

        # All methods have async equivalents
        batch = await client.normalize_batch(["住所1", "住所2"])
        postal = await client.postal("1500043")
        suggestions = await client.suggest("渋谷")
        validation = await client.validate("東京都渋谷区道玄坂1-2-3")

asyncio.run(main())
```

## Error Handling

All exceptions inherit from `JushoError`:

```python
from jusho import (
    Jusho,
    JushoError,
    NotFoundError,
    RateLimitError,
    ValidationError,
    NetworkError,
    TimeoutError,
    APIError,
)

client = Jusho()

try:
    result = client.normalize("...")
except NotFoundError:
    print("Address not found")
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after}s")
except ValidationError:
    print("Invalid request")
except NetworkError:
    print("Network issue")
except TimeoutError:
    print("Request timed out")
except APIError as e:
    print(f"API error: {e.status_code}")
except JushoError:
    print("Unexpected Jusho error")
```

## Raw Response Access

Every result object includes a `.raw` attribute containing the original JSON dict:

```python
result = client.normalize("東京都渋谷区道玄坂1-2-3")
print(result.raw)  # Full JSON response as a dict
```

---

# Jusho Python SDK (日本語)

[Jusho](https://jusho.dev) 日本語住所正規化APIのPythonクライアントです。

自由形式の日本語住所文字列を、郵便番号、都道府県・市区町村・町域の分解、カタカナ読み、行政コード、緯度経度を含む構造化データに正規化します。

## インストール

```bash
pip install normal-jusho
```

## 基本的な使い方

```python
from jusho import Jusho

client = Jusho()

result = client.normalize("東京都渋谷区道玄坂1-2-3")

print(result.address.full)       # "東京都渋谷区道玄坂一丁目2-3"
print(result.address.pref)       # "東京都"
print(result.address.city)       # "渋谷区"
print(result.codes.post_code)    # "1500043"
print(result.geo.lat)            # "35.6580"
print(result.kana.pref)          # "トウキョウト"
```

## 主な機能

- **同期・非同期**クライアント (`Jusho` / `AsyncJusho`)
- **型付きレスポンス** (PEP 561準拠、型ヒント完全対応)
- **構造化エラーハンドリング** (明確な例外階層)
- **最小依存** (`httpx`のみ)
- **Python 3.9+** 対応

## 一括正規化

最大100件の住所を一度に正規化できます:

```python
result = client.normalize_batch([
    "東京都千代田区千代田1-1",
    "大阪府大阪市北区梅田1-1-1",
])

for item in result.results:
    if item.success:
        print(item.result.address.full)
    else:
        print(f"エラー: {item.error}")
```

## 非同期

```python
import asyncio
from jusho import AsyncJusho

async def main():
    async with AsyncJusho() as client:
        result = await client.normalize("東京都渋谷区道玄坂1-2-3")
        print(result.address.full)

asyncio.run(main())
```

## エラーハンドリング

すべての例外は `JushoError` を継承しています:

```python
from jusho import Jusho, NotFoundError, RateLimitError

client = Jusho()

try:
    result = client.normalize("...")
except NotFoundError:
    print("住所が見つかりませんでした")
except RateLimitError as e:
    print(f"レート制限超過。{e.retry_after}秒後に再試行してください")
```

## ライセンス

MIT
