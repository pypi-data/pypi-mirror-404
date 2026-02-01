# FirmeAPI Python SDK

Official Python SDK for [FirmeAPI.ro](https://www.firmeapi.ro) - Romanian company data API.

## Requirements

- Python 3.9+

## Installation

```bash
pip install firmeapi
```

## Quick Start

```python
from firmeapi import FirmeApi

client = FirmeApi(api_key="your_api_key_here")

# Get company details
company = client.get_company("12345678")
print(company.denumire)
```

## Sandbox Mode

Use sandbox mode to test your integration without consuming credits:

```python
client = FirmeApi(api_key="your_api_key_here", sandbox=True)

# Test CUIs available in sandbox:
# 00000001 - Active company with all data
# 00000002 - Inactive/deleted company
# 00000003 - Company with multiple VAT periods
# 00000004 - Company with ANAF debts
# 00000005 - Company with MOF publications
# 99999999 - Returns 404 (for testing errors)
```

## API Methods

### `get_company(cui: str) -> Company`

Get detailed company information by CUI.

```python
company = client.get_company("12345678")

print(company.denumire)              # Company name
print(company.stare)                 # Registration status
print(company.tva.platitor)          # VAT payer status
print(company.adresa_sediu_social)   # Headquarters address
```

### `get_bilant(cui: str) -> Bilant`

Get company balance sheet data.

```python
bilant = client.get_bilant("12345678")

for year in bilant.ani:
    print(f"{year.an}:")
    print(f"  Revenue: {year.detalii.I1} RON")
    print(f"  Profit: {year.detalii.I5} RON")
    print(f"  Employees: {year.detalii.I10}")
```

### `get_restante(cui: str) -> RestanteResponse`

Get company ANAF debts.

```python
restante = client.get_restante("12345678")

if restante.restante:
    print("Company has outstanding debts:")
    for debt in restante.restante:
        print(f"  {debt.tip_obligatie}: {debt.suma_restanta} RON")
```

### `get_mof(cui: str) -> MofResponse`

Get company Monitorul Oficial publications.

```python
mof = client.get_mof("12345678")

for publication in mof.rezultate:
    print(f"{publication.data}: {publication.titlu_publicatie}")
```

### `search_companies(**filters) -> SearchResponse`

Search companies with filters.

```python
results = client.search_companies(
    judet="B",           # County code
    caen="6201",         # CAEN code
    tva=True,            # VAT payer only
    telefon=True,        # Has phone number
    data_start="2024-01-01",
    data_end="2024-12-31",
    page=1,
)

print(f"Found {results.pagination.total} companies")

for company in results.items:
    print(f"{company.cui}: {company.denumire}")
```

### `get_free_company(cui: str) -> FreeCompany`

Get basic company info using the free API (no API key required, rate limited).

```python
company = client.get_free_company("12345678")
print(company.denumire)
```

## Async Support

The SDK includes an async client for use with asyncio:

```python
import asyncio
from firmeapi import AsyncFirmeApi

async def main():
    async with AsyncFirmeApi(api_key="your_api_key") as client:
        company = await client.get_company("12345678")
        print(company.denumire)

asyncio.run(main())
```

## Error Handling

The SDK raises typed exceptions for different scenarios:

```python
from firmeapi import (
    FirmeApi,
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    InsufficientCreditsError,
    ValidationError,
    FirmeApiError,
)

try:
    company = client.get_company("12345678")
except NotFoundError:
    print("Company not found")
except AuthenticationError:
    print("Invalid API key")
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after} seconds")
except InsufficientCreditsError as e:
    print(f"Not enough credits. Have: {e.available_credits}, need: {e.required_credits}")
except ValidationError as e:
    print(f"Invalid input: {e.message}")
except FirmeApiError as e:
    print(f"API error: {e.message}")
```

## Configuration Options

```python
client = FirmeApi(
    api_key="your_api_key",
    sandbox=False,                    # Enable sandbox mode (default: False)
    base_url="https://www.firmeapi.ro/api",  # Custom base URL
    timeout=30.0,                     # Request timeout in seconds (default: 30.0)
)
```

## Context Manager

The client can be used as a context manager to ensure proper cleanup:

```python
with FirmeApi(api_key="your_api_key") as client:
    company = client.get_company("12345678")
    print(company.denumire)
```

## Type Hints

Full type hints are included for all methods and return values:

```python
from firmeapi import Company, Bilant, SearchResponse

def process_company(company: Company) -> None:
    print(company.denumire)
```

## License

MIT
