import os
from typing import Any
import httpx


class RadarrClient:
    """Client HTTP pour l'API Radarr v3."""

    def __init__(self, base_url: str | None = None, api_key: str | None = None):
        self.base_url = (base_url or os.getenv("RADARR_URL", "")).rstrip("/")
        self.api_key = api_key or os.getenv("RADARR_API_KEY", "")

        if not self.base_url:
            raise ValueError("RADARR_URL is required")
        if not self.api_key:
            raise ValueError("RADARR_API_KEY is required")

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
        """Execute une requête HTTP vers l'API Radarr."""
        url = f"{self.base_url}/api/v3{endpoint}"

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
        """Récupère le statut du système Radarr."""
        return await self._request("GET", "/system/status")

    async def get_movies(self) -> list[dict[str, Any]]:
        """Récupère tous les films de la bibliothèque."""
        return await self._request("GET", "/movie")

    async def get_movie(self, movie_id: int) -> dict[str, Any]:
        """Récupère les détails d'un film par son ID."""
        return await self._request("GET", f"/movie/{movie_id}")

    async def search_movie(self, term: str) -> list[dict[str, Any]]:
        """Recherche un film sur TMDB via Radarr."""
        return await self._request("GET", "/movie/lookup", params={"term": term})

    async def add_movie(
        self,
        tmdb_id: int,
        title: str,
        quality_profile_id: int,
        root_folder_path: str,
        monitored: bool = True,
        search_for_movie: bool = True,
    ) -> dict[str, Any]:
        """Ajoute un film à la bibliothèque Radarr."""
        # Récupérer les infos du film depuis TMDB
        lookup_results = await self.search_movie(f"tmdb:{tmdb_id}")
        if not lookup_results:
            raise ValueError(f"Film non trouvé avec TMDB ID: {tmdb_id}")

        movie_data = lookup_results[0]
        movie_data.update({
            "qualityProfileId": quality_profile_id,
            "rootFolderPath": root_folder_path,
            "monitored": monitored,
            "addOptions": {
                "searchForMovie": search_for_movie,
            },
        })

        return await self._request("POST", "/movie", json_data=movie_data)

    async def delete_movie(
        self,
        movie_id: int,
        delete_files: bool = False,
        add_import_exclusion: bool = False,
    ) -> None:
        """Supprime un film de la bibliothèque."""
        params = {
            "deleteFiles": str(delete_files).lower(),
            "addImportExclusion": str(add_import_exclusion).lower(),
        }
        await self._request("DELETE", f"/movie/{movie_id}", params=params)

    async def get_queue(self) -> dict[str, Any]:
        """Récupère la queue de téléchargement."""
        return await self._request("GET", "/queue", params={"pageSize": 100})

    async def get_calendar(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[dict[str, Any]]:
        """Récupère le calendrier des sorties de films."""
        params = {}
        if start_date:
            params["start"] = start_date
        if end_date:
            params["end"] = end_date
        return await self._request("GET", "/calendar", params=params or None)

    async def get_root_folders(self) -> list[dict[str, Any]]:
        """Récupère les dossiers racine configurés."""
        return await self._request("GET", "/rootfolder")

    async def get_quality_profiles(self) -> list[dict[str, Any]]:
        """Récupère les profils de qualité disponibles."""
        return await self._request("GET", "/qualityprofile")
