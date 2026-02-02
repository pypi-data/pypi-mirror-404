import os
from typing import Any
import httpx


class ProwlarrClient:
    """Client HTTP pour l'API Prowlarr v1."""

    def __init__(self, base_url: str | None = None, api_key: str | None = None):
        self.base_url = (base_url or os.getenv("PROWLARR_URL", "")).rstrip("/")
        self.api_key = api_key or os.getenv("PROWLARR_API_KEY", "")

        if not self.base_url:
            raise ValueError("PROWLARR_URL is required")
        if not self.api_key:
            raise ValueError("PROWLARR_API_KEY is required")

        self.headers = {
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json",
        }

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
    ) -> Any:
        """Execute une requête HTTP vers l'API Prowlarr."""
        url = f"{self.base_url}/api/v1{endpoint}"

        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=url,
                headers=self.headers,
                params=params,
                json=json_data,
                timeout=30.0,
            )
            response.raise_for_status()

            if response.status_code == 204:
                return None
            return response.json()

    async def get_system_status(self) -> dict[str, Any]:
        """Récupère le statut du système Prowlarr."""
        return await self._request("GET", "/system/status")

    async def get_health(self) -> list[dict[str, Any]]:
        """Récupère les problèmes de santé détectés."""
        return await self._request("GET", "/health")

    async def get_indexers(self) -> list[dict[str, Any]]:
        """Récupère la liste des indexeurs configurés."""
        return await self._request("GET", "/indexer")

    async def get_indexer(self, indexer_id: int) -> dict[str, Any]:
        """Récupère les détails d'un indexeur par son ID."""
        return await self._request("GET", f"/indexer/{indexer_id}")

    async def test_indexer(self, indexer_id: int) -> Any:
        """Teste un indexeur spécifique."""
        indexer = await self.get_indexer(indexer_id)
        return await self._request("POST", "/indexer/test", json_data=indexer)

    async def test_all_indexers(self) -> list[dict[str, Any]]:
        """Teste tous les indexeurs."""
        return await self._request("POST", "/indexer/testall")

    async def search(
        self,
        query: str,
        indexer_ids: list[int] | None = None,
        categories: list[int] | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Recherche sur les indexeurs."""
        params: dict[str, Any] = {
            "query": query,
            "limit": limit,
        }
        if indexer_ids:
            params["indexerIds"] = indexer_ids
        if categories:
            params["categories"] = categories
        return await self._request("GET", "/search", params=params)

    async def get_indexer_stats(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
        """Récupère les statistiques des indexeurs."""
        params = {}
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date
        return await self._request("GET", "/indexerstats", params=params or None)

    async def get_applications(self) -> list[dict[str, Any]]:
        """Récupère la liste des applications connectées."""
        return await self._request("GET", "/applications")

    async def get_history(
        self,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        """Récupère l'historique des recherches."""
        params = {
            "page": page,
            "pageSize": page_size,
            "sortKey": "date",
            "sortDirection": "descending",
        }
        return await self._request("GET", "/history", params=params)
