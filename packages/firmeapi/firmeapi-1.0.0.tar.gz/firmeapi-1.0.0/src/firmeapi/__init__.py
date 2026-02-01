"""
FirmeAPI - Official Python SDK

Official Python SDK for FirmeAPI.ro - Romanian company data API

Example:
    >>> from firmeapi import FirmeApi
    >>>
    >>> client = FirmeApi(api_key="your_api_key_here")
    >>>
    >>> # Get company details
    >>> company = client.get_company("12345678")
    >>> print(company.denumire)
    >>>
    >>> # Search companies
    >>> results = client.search_companies(judet="B", caen="6201")
    >>> print(f"Found {results.pagination.total} companies")
"""

from .client import AsyncFirmeApi, FirmeApi
from .exceptions import (
    ApiError,
    AuthenticationError,
    FirmeApiError,
    InsufficientCreditsError,
    NetworkError,
    NotFoundError,
    RateLimitError,
    TimeoutError,
    ValidationError,
)
from .types import (
    Address,
    Bilant,
    BilantDetalii,
    BilantYear,
    Company,
    FreeApiUsage,
    FreeCompany,
    MofPublication,
    MofResponse,
    Pagination,
    Restanta,
    RestanteResponse,
    SearchResponse,
    StatusInactiv,
    TvaInfo,
    TvaPeriod,
)

__version__ = "1.0.0"
__all__ = [
    # Clients
    "FirmeApi",
    "AsyncFirmeApi",
    # Exceptions
    "FirmeApiError",
    "AuthenticationError",
    "NotFoundError",
    "RateLimitError",
    "InsufficientCreditsError",
    "ValidationError",
    "ApiError",
    "NetworkError",
    "TimeoutError",
    # Types
    "Address",
    "TvaPeriod",
    "TvaInfo",
    "StatusInactiv",
    "Company",
    "BilantDetalii",
    "BilantYear",
    "Bilant",
    "Restanta",
    "RestanteResponse",
    "MofPublication",
    "MofResponse",
    "Pagination",
    "SearchResponse",
    "FreeCompany",
    "FreeApiUsage",
]
