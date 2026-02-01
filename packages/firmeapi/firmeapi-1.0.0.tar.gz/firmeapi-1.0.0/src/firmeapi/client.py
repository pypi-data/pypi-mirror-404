"""
FirmeAPI Client

Official Python client for FirmeAPI.ro
"""

import re
from typing import Any, Optional

import httpx

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
    Bilant,
    Company,
    FreeApiUsage,
    FreeCompany,
    MofResponse,
    RestanteResponse,
    SearchResponse,
)

DEFAULT_BASE_URL = "https://www.firmeapi.ro/api"
DEFAULT_TIMEOUT = 30.0
SDK_VERSION = "1.0.0"


class FirmeApi:
    """
    FirmeAPI Python Client

    Official Python SDK for FirmeAPI.ro - Romanian company data API

    Example:
        >>> from firmeapi import FirmeApi
        >>>
        >>> client = FirmeApi(api_key="your_api_key")
        >>>
        >>> # Get company details
        >>> company = client.get_company("12345678")
        >>> print(company.denumire)
        >>>
        >>> # Enable sandbox mode
        >>> client = FirmeApi(api_key="your_api_key", sandbox=True)
    """

    def __init__(
        self,
        api_key: str,
        *,
        sandbox: bool = False,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        """
        Create a new FirmeAPI client

        Args:
            api_key: Your FirmeAPI API key
            sandbox: Enable sandbox mode for testing (default: False)
            base_url: Base URL override (default: https://www.firmeapi.ro/api)
            timeout: Request timeout in seconds (default: 30.0)
        """
        if not api_key:
            raise ValidationError("API key is required", "MISSING_API_KEY")

        self.api_key = api_key
        self.sandbox = sandbox
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        self._client = httpx.Client(
            timeout=timeout,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": f"firmeapi-python/{SDK_VERSION}",
            },
        )

    def __enter__(self) -> "FirmeApi":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def close(self) -> None:
        """Close the HTTP client"""
        self._client.close()

    def get_company(self, cui: str) -> Company:
        """
        Get company details by CUI

        Args:
            cui: The company's CUI (unique identification code)

        Returns:
            Company details

        Example:
            >>> company = client.get_company("12345678")
            >>> print(company.denumire)
        """
        clean_cui = self._clean_cui(cui)
        response = self._request(f"/v1/firma/{clean_cui}")
        return Company.from_dict(response["data"])

    def get_bilant(self, cui: str) -> Bilant:
        """
        Get company balance sheet (bilant) by CUI

        Args:
            cui: The company's CUI

        Returns:
            Balance sheet data for multiple years

        Example:
            >>> bilant = client.get_bilant("12345678")
            >>> for year in bilant.ani:
            ...     print(f"{year.an}: {year.detalii.I1} RON")
        """
        clean_cui = self._clean_cui(cui)
        response = self._request(f"/v1/bilant/{clean_cui}")
        return Bilant.from_dict(response["data"])

    def get_restante(self, cui: str) -> RestanteResponse:
        """
        Get company ANAF debts (restante) by CUI

        Args:
            cui: The company's CUI

        Returns:
            ANAF debt information

        Example:
            >>> restante = client.get_restante("12345678")
            >>> if restante.restante:
            ...     print("Company has outstanding debts!")
        """
        clean_cui = self._clean_cui(cui)
        response = self._request(f"/v1/restante/{clean_cui}")
        return RestanteResponse.from_dict(response["data"])

    def get_mof(self, cui: str) -> MofResponse:
        """
        Get company Monitorul Oficial publications by CUI

        Args:
            cui: The company's CUI

        Returns:
            MOF publications

        Example:
            >>> mof = client.get_mof("12345678")
            >>> for pub in mof.rezultate:
            ...     print(f"{pub.data}: {pub.titlu_publicatie}")
        """
        clean_cui = self._clean_cui(cui)
        response = self._request(f"/v1/mof/{clean_cui}")
        return MofResponse.from_dict(response["data"])

    def search_companies(
        self,
        *,
        q: Optional[str] = None,
        judet: Optional[str] = None,
        localitate: Optional[str] = None,
        caen: Optional[str] = None,
        stare: Optional[str] = None,
        data: Optional[str] = None,
        data_start: Optional[str] = None,
        data_end: Optional[str] = None,
        tva: Optional[bool] = None,
        telefon: Optional[bool] = None,
        page: int = 1,
    ) -> SearchResponse:
        """
        Search companies with filters

        Args:
            q: Search term (company name, CUI, registration number)
            judet: County code (e.g., 'BV', 'CJ', 'B')
            localitate: City/locality name
            caen: CAEN code
            stare: Registration status (e.g., 'INREGISTRAT', 'RADIAT')
            data: Exact registration date (YYYY-MM-DD)
            data_start: Registration date from (YYYY-MM-DD)
            data_end: Registration date to (YYYY-MM-DD)
            tva: VAT payer filter
            telefon: Has phone number filter
            page: Page number (default: 1)

        Returns:
            Paginated list of companies

        Example:
            >>> results = client.search_companies(judet="B", caen="6201", tva=True)
            >>> print(f"Found {results.pagination.total} companies")
        """
        params: dict[str, str] = {}

        if q is not None:
            params["q"] = q
        if judet is not None:
            params["judet"] = judet
        if localitate is not None:
            params["localitate"] = localitate
        if caen is not None:
            params["caen"] = caen
        if stare is not None:
            params["stare"] = stare
        if data is not None:
            params["data"] = data
        if data_start is not None:
            params["data_start"] = data_start
        if data_end is not None:
            params["data_end"] = data_end
        if tva is not None:
            params["tva"] = "1" if tva else "0"
        if telefon is not None:
            params["telefon"] = "1" if telefon else "0"
        if page != 1:
            params["page"] = str(page)

        response = self._request("/v1/firme", params=params)
        return SearchResponse.from_dict(response["data"])

    def get_free_company(self, cui: str) -> FreeCompany:
        """
        Get basic company info using the free API

        Requires a Free API Key (generated separately from dashboard).
        Free API does not support sandbox mode.

        Args:
            cui: The company's CUI

        Returns:
            Basic company information

        Example:
            >>> client = FirmeApi(api_key="fa_xxxxxxxx")  # Free API Key
            >>> company = client.get_free_company("12345678")
            >>> print(company.denumire)
        """
        clean_cui = self._clean_cui(cui)
        response = self._request(f"/free/firma/{clean_cui}", is_free_api=True)
        return FreeCompany.from_dict(response["data"])

    def get_free_api_usage(self) -> FreeApiUsage:
        """
        Get free API usage statistics

        Requires a Free API Key.

        Returns:
            Usage information
        """
        response = self._request("/free/usage", is_free_api=True)
        return FreeApiUsage.from_dict(response["data"])

    def _clean_cui(self, cui: str) -> str:
        """Clean and validate CUI"""
        cleaned = re.sub(r"[^0-9]", "", cui)

        if len(cleaned) < 2 or len(cleaned) > 10:
            raise ValidationError(
                "CUI must contain between 2 and 10 digits",
                "INVALID_CUI_FORMAT",
            )

        return cleaned

    def _request(
        self,
        endpoint: str,
        *,
        params: Optional[dict[str, str]] = None,
        is_free_api: bool = False,
    ) -> dict[str, Any]:
        """Make HTTP request to the API"""
        url = f"{self.base_url}{endpoint}"

        headers: dict[str, str] = {}

        # Always add auth header (both paid and free API require it)
        headers["X-API-KEY"] = self.api_key

        # Add sandbox header only for paid API (v1), not for free API
        if self.sandbox and not is_free_api:
            headers["X-Sandbox"] = "true"

        try:
            response = self._client.get(url, headers=headers, params=params)
        except httpx.TimeoutException as e:
            raise TimeoutError(f"Request timed out after {self.timeout}s") from e
        except httpx.RequestError as e:
            raise NetworkError(str(e)) from e

        try:
            data: dict[str, Any] = response.json()
        except ValueError as e:
            raise ApiError(
                "Invalid JSON response from API",
                "INVALID_RESPONSE",
                response.status_code,
            ) from e

        if response.status_code >= 400:
            self._handle_error_response(response.status_code, data)

        return data

    def _handle_error_response(
        self, status_code: int, data: dict[str, Any]
    ) -> None:
        """Handle error response from API"""
        message = data.get("message") or data.get("error") or "Unknown error"
        code = data.get("code", "UNKNOWN_ERROR")

        if status_code == 401:
            raise AuthenticationError(message, code)

        if status_code == 403:
            if code in ("CREDITS_EXHAUSTED", "MOF_INSUFFICIENT_CREDITS"):
                raise InsufficientCreditsError(
                    message,
                    code,
                    data.get("available_credits", 0),
                    data.get("required_credits", 1),
                )
            raise AuthenticationError(message, code)

        if status_code == 404:
            raise NotFoundError(message, code)

        if status_code == 429:
            raise RateLimitError(
                message,
                code,
                data.get("retry_after", 1),
                data.get("current_usage", 0),
                data.get("limit", 0),
            )

        if status_code == 400:
            raise ValidationError(message, code)

        raise ApiError(message, code, status_code)


class AsyncFirmeApi:
    """
    Async FirmeAPI Python Client

    Example:
        >>> from firmeapi import AsyncFirmeApi
        >>>
        >>> async with AsyncFirmeApi(api_key="your_api_key") as client:
        ...     company = await client.get_company("12345678")
        ...     print(company.denumire)
    """

    def __init__(
        self,
        api_key: str,
        *,
        sandbox: bool = False,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        if not api_key:
            raise ValidationError("API key is required", "MISSING_API_KEY")

        self.api_key = api_key
        self.sandbox = sandbox
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        self._client = httpx.AsyncClient(
            timeout=timeout,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": f"firmeapi-python/{SDK_VERSION}",
            },
        )

    async def __aenter__(self) -> "AsyncFirmeApi":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def close(self) -> None:
        """Close the HTTP client"""
        await self._client.aclose()

    async def get_company(self, cui: str) -> Company:
        """Get company details by CUI"""
        clean_cui = self._clean_cui(cui)
        response = await self._request(f"/v1/firma/{clean_cui}")
        return Company.from_dict(response["data"])

    async def get_bilant(self, cui: str) -> Bilant:
        """Get company balance sheet by CUI"""
        clean_cui = self._clean_cui(cui)
        response = await self._request(f"/v1/bilant/{clean_cui}")
        return Bilant.from_dict(response["data"])

    async def get_restante(self, cui: str) -> RestanteResponse:
        """Get company ANAF debts by CUI"""
        clean_cui = self._clean_cui(cui)
        response = await self._request(f"/v1/restante/{clean_cui}")
        return RestanteResponse.from_dict(response["data"])

    async def get_mof(self, cui: str) -> MofResponse:
        """Get company MOF publications by CUI"""
        clean_cui = self._clean_cui(cui)
        response = await self._request(f"/v1/mof/{clean_cui}")
        return MofResponse.from_dict(response["data"])

    async def search_companies(
        self,
        *,
        q: Optional[str] = None,
        judet: Optional[str] = None,
        localitate: Optional[str] = None,
        caen: Optional[str] = None,
        stare: Optional[str] = None,
        data: Optional[str] = None,
        data_start: Optional[str] = None,
        data_end: Optional[str] = None,
        tva: Optional[bool] = None,
        telefon: Optional[bool] = None,
        page: int = 1,
    ) -> SearchResponse:
        """Search companies with filters"""
        params: dict[str, str] = {}

        if q is not None:
            params["q"] = q
        if judet is not None:
            params["judet"] = judet
        if localitate is not None:
            params["localitate"] = localitate
        if caen is not None:
            params["caen"] = caen
        if stare is not None:
            params["stare"] = stare
        if data is not None:
            params["data"] = data
        if data_start is not None:
            params["data_start"] = data_start
        if data_end is not None:
            params["data_end"] = data_end
        if tva is not None:
            params["tva"] = "1" if tva else "0"
        if telefon is not None:
            params["telefon"] = "1" if telefon else "0"
        if page != 1:
            params["page"] = str(page)

        response = await self._request("/v1/firme", params=params)
        return SearchResponse.from_dict(response["data"])

    async def get_free_company(self, cui: str) -> FreeCompany:
        """Get basic company info using the free API (requires Free API Key)"""
        clean_cui = self._clean_cui(cui)
        response = await self._request(f"/free/firma/{clean_cui}", is_free_api=True)
        return FreeCompany.from_dict(response["data"])

    async def get_free_api_usage(self) -> FreeApiUsage:
        """Get free API usage statistics (requires Free API Key)"""
        response = await self._request("/free/usage", is_free_api=True)
        return FreeApiUsage.from_dict(response["data"])

    def _clean_cui(self, cui: str) -> str:
        """Clean and validate CUI"""
        cleaned = re.sub(r"[^0-9]", "", cui)

        if len(cleaned) < 2 or len(cleaned) > 10:
            raise ValidationError(
                "CUI must contain between 2 and 10 digits",
                "INVALID_CUI_FORMAT",
            )

        return cleaned

    async def _request(
        self,
        endpoint: str,
        *,
        params: Optional[dict[str, str]] = None,
        is_free_api: bool = False,
    ) -> dict[str, Any]:
        """Make HTTP request to the API"""
        url = f"{self.base_url}{endpoint}"

        headers: dict[str, str] = {}

        # Always add auth header (both paid and free API require it)
        headers["X-API-KEY"] = self.api_key

        # Add sandbox header only for paid API (v1), not for free API
        if self.sandbox and not is_free_api:
            headers["X-Sandbox"] = "true"

        try:
            response = await self._client.get(url, headers=headers, params=params)
        except httpx.TimeoutException as e:
            raise TimeoutError(f"Request timed out after {self.timeout}s") from e
        except httpx.RequestError as e:
            raise NetworkError(str(e)) from e

        try:
            data: dict[str, Any] = response.json()
        except ValueError as e:
            raise ApiError(
                "Invalid JSON response from API",
                "INVALID_RESPONSE",
                response.status_code,
            ) from e

        if response.status_code >= 400:
            self._handle_error_response(response.status_code, data)

        return data

    def _handle_error_response(
        self, status_code: int, data: dict[str, Any]
    ) -> None:
        """Handle error response from API"""
        message = data.get("message") or data.get("error") or "Unknown error"
        code = data.get("code", "UNKNOWN_ERROR")

        if status_code == 401:
            raise AuthenticationError(message, code)

        if status_code == 403:
            if code in ("CREDITS_EXHAUSTED", "MOF_INSUFFICIENT_CREDITS"):
                raise InsufficientCreditsError(
                    message,
                    code,
                    data.get("available_credits", 0),
                    data.get("required_credits", 1),
                )
            raise AuthenticationError(message, code)

        if status_code == 404:
            raise NotFoundError(message, code)

        if status_code == 429:
            raise RateLimitError(
                message,
                code,
                data.get("retry_after", 1),
                data.get("current_usage", 0),
                data.get("limit", 0),
            )

        if status_code == 400:
            raise ValidationError(message, code)

        raise ApiError(message, code, status_code)
